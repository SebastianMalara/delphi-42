from __future__ import annotations

import argparse
import glob
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import request

from bot.oracle_bot import load_config
from core.retriever import SQLiteRetriever
from core.runtime_config import ConfigError, OracleRuntimeConfig


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
) -> tuple[OracleRuntimeConfig, list[CheckResult]]:
    config = load_config(config_path)
    results = [
        CheckResult("config", True, config.summary()),
        _check_import("openai", import_module_fn),
        _check_import("libzim.reader", import_module_fn),
        _check_import("meshtastic.serial_interface", import_module_fn),
        _check_import("pubsub", import_module_fn),
        _check_model_service(config, urlopen_fn),
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


def _check_serial_devices(
    config: OracleRuntimeConfig,
    glob_fn: Callable[[str], list[str]],
) -> CheckResult:
    discovered = sorted(
        {
            *glob_fn("/dev/cu.usb*"),
            *glob_fn("/dev/tty.usb*"),
        }
    )
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Delphi-42 macOS preflight checks.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/oracle.mac.sim.yaml"),
        help="Path to the runtime config to validate.",
    )
    args = parser.parse_args()

    try:
        config, results = run_preflight(args.config)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Delphi-42 mac preflight for {config.source_path}")
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
