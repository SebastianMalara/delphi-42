from __future__ import annotations

import argparse
import glob
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import request
from urllib.parse import urlparse

from bot.oracle_bot import load_config
from core.llm_runner import ModelExecutionError, ModelUnavailableError, OpenAICompatibleRunner
from core.prompt_builder import build_prompt
from core.retriever import SQLiteRetriever
from core.runtime_config import ConfigError, OracleRuntimeConfig


SERIAL_DEVICE_GLOBS = (
    "/dev/cu.usb*",
    "/dev/tty.usb*",
    "/dev/serial/by-id/*",
    "/dev/ttyUSB*",
    "/dev/ttyACM*",
)
PROVIDER_EXPECTED_BASE_PATH = {
    "stackflow": "/v1",
    "lm-studio": "/v1",
    "ovms": "/v3",
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    details: str


def run_preflight(
    config_path: Path,
    *,
    import_module_fn: Callable[[str], object] = importlib.import_module,
    urlopen_fn: Callable[..., object] = request.urlopen,
    glob_fn: Callable[[str], list[str]] = glob.glob,
    runner_factory: Callable[..., object] = OpenAICompatibleRunner,
) -> tuple[OracleRuntimeConfig, list[CheckResult]]:
    config = load_config(config_path)
    results = [
        CheckResult("config", True, config.summary()),
        _check_placeholder_values(config),
        _check_provider_base_url(config),
        _check_import("openai", import_module_fn),
        _check_import("libzim.reader", import_module_fn),
        _check_import("meshtastic.serial_interface", import_module_fn),
        _check_import("pubsub", import_module_fn),
        _check_model_service(config, urlopen_fn),
        _check_completion_probe(config, runner_factory),
        _check_index(config.knowledge.index_path),
        _check_runtime_zim_files(config),
        _check_serial_devices(config, glob_fn),
    ]
    return config, results


def _check_import(module_name: str, import_module_fn: Callable[[str], object]) -> CheckResult:
    try:
        import_module_fn(module_name)
    except Exception as exc:
        return CheckResult(module_name, False, f"import failed: {exc}")
    return CheckResult(module_name, True, "import OK")


def _check_provider_base_url(config: OracleRuntimeConfig) -> CheckResult:
    if config.llm.backend == "deterministic" or config.llm.provider == "generic":
        return CheckResult("llm-provider", True, f"provider={config.llm.provider}")

    expected_path = PROVIDER_EXPECTED_BASE_PATH.get(config.llm.provider)
    if expected_path is None:
        return CheckResult("llm-provider", True, f"provider={config.llm.provider}")

    actual_path = urlparse(config.llm.base_url).path.rstrip("/") or "/"
    if actual_path == expected_path:
        return CheckResult(
            "llm-provider",
            True,
            f"provider={config.llm.provider} matches base path {expected_path}",
        )

    return CheckResult(
        "llm-provider",
        False,
        (
            f"provider '{config.llm.provider}' expects llm.base_url ending with "
            f"'{expected_path}'; got '{config.llm.base_url}'"
        ),
    )


def _check_model_service(
    config: OracleRuntimeConfig,
    urlopen_fn: Callable[..., object],
) -> CheckResult:
    if config.llm.backend == "deterministic":
        return CheckResult("llm-service", True, "deterministic backend selected")

    models_url = f"{config.llm.base_url.rstrip('/')}/models"
    headers = {"Accept": "application/json"}
    if config.llm.api_key:
        headers["Authorization"] = f"Bearer {config.llm.api_key}"
    req = request.Request(models_url, headers=headers, method="GET")

    try:
        with urlopen_fn(req, timeout=config.llm.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return CheckResult("llm-service", False, f"request failed: {exc}")

    model_ids = [str(model.get("id", "")).strip() for model in payload.get("data", [])]
    if not model_ids:
        return CheckResult("llm-service", False, "no models returned by the configured API")
    if config.llm.model not in model_ids:
        return CheckResult(
            "llm-service",
            False,
            f"configured model '{config.llm.model}' not found; available: {', '.join(model_ids)}",
        )
    return CheckResult("llm-service", True, f"model visible: {config.llm.model}")


def _check_completion_probe(
    config: OracleRuntimeConfig,
    runner_factory: Callable[..., object],
) -> CheckResult:
    if config.llm.backend == "deterministic":
        return CheckResult("llm-completion", True, "deterministic backend selected")

    try:
        runner = runner_factory(
            base_url=config.llm.base_url,
            model=config.llm.model,
            api_key=config.llm.api_key,
            timeout_seconds=config.llm.timeout_seconds,
        )
        answer = runner.generate(
            build_prompt(
                "Reply with a short readiness confirmation.",
                [],
            )
        )
    except (ModelUnavailableError, ModelExecutionError) as exc:
        return CheckResult("llm-completion", False, str(exc))
    except Exception as exc:
        return CheckResult("llm-completion", False, f"completion probe failed: {exc}")

    short_answer = getattr(answer, "short_answer", "")
    if not isinstance(short_answer, str) or not short_answer.strip():
        return CheckResult("llm-completion", False, "completion probe returned an empty answer")
    return CheckResult("llm-completion", True, "completion probe succeeded")


def _check_index(index_path: Path) -> CheckResult:
    try:
        SQLiteRetriever(index_path)
    except Exception as exc:
        return CheckResult("sqlite-index", False, f"{index_path}: {exc}")
    return CheckResult("sqlite-index", True, str(index_path))


def _check_runtime_zim_files(config: OracleRuntimeConfig) -> CheckResult:
    if not config.knowledge.runtime_zim_fallback_enabled:
        return CheckResult(
            "zim-files",
            True,
            f"runtime fallback disabled; configured dir is {config.knowledge.zim_dir}",
        )

    missing = [
        filename
        for filename in config.knowledge.runtime_zim_allowlist
        if not (config.knowledge.zim_dir / filename).exists()
    ]
    if missing:
        return CheckResult(
            "zim-files",
            False,
            "missing allowlisted archives: " + ", ".join(missing),
        )
    if not config.knowledge.runtime_zim_allowlist:
        return CheckResult("zim-files", False, "runtime fallback enabled without an allowlist")
    return CheckResult(
        "zim-files",
        True,
        "allowlisted archives present: " + ", ".join(config.knowledge.runtime_zim_allowlist),
    )


def _check_placeholder_values(config: OracleRuntimeConfig) -> CheckResult:
    placeholders: list[str] = []
    if config.radio.transport == "meshtastic" and "REPLACE_ME" in config.radio.device:
        placeholders.append("radio.device")
    if config.llm.backend != "deterministic" and config.llm.model.startswith("replace-with-"):
        placeholders.append("llm.model")

    if placeholders:
        return CheckResult(
            "config-placeholders",
            False,
            "replace placeholder values before live use: " + ", ".join(placeholders),
        )
    return CheckResult("config-placeholders", True, "no placeholder values detected")


def _check_serial_devices(
    config: OracleRuntimeConfig,
    glob_fn: Callable[[str], list[str]],
) -> CheckResult:
    discovered = sorted({device for pattern in SERIAL_DEVICE_GLOBS for device in glob_fn(pattern)})
    if config.radio.transport != "meshtastic":
        details = ", ".join(discovered) if discovered else "none discovered"
        return CheckResult("serial-devices", True, f"simulated transport; visible devices: {details}")

    device = config.radio.device
    if device in discovered or Path(device).exists():
        return CheckResult("serial-devices", True, f"configured device present: {device}")

    details = ", ".join(discovered) if discovered else "none discovered"
    return CheckResult(
        "serial-devices",
        False,
        f"configured device missing: {device}; visible devices: {details}",
    )


def main(
    *,
    default_config: Path | None = None,
    banner_label: str = "host",
) -> None:
    parser = argparse.ArgumentParser(description="Run the Delphi-42 host preflight checks.")
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config or Path("config/oracle.mac.sim.yaml"),
        help="Path to the runtime config to validate.",
    )
    args = parser.parse_args()

    try:
        config, results = run_preflight(args.config)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Delphi-42 {banner_label} preflight for {config.source_path}")
    failures = 0
    for result in results:
        status = "PASS" if result.ok else "FAIL"
        if not result.ok:
            failures += 1
        print(f"[{status}] {result.name}: {result.details}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
