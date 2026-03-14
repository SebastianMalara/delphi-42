from __future__ import annotations

import argparse
import json
import re
import stat
import textwrap
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib import request
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "artifacts/ubuntu-ovms"
DEFAULT_BASE_URL = "http://127.0.0.1:8000/v3"
DEFAULT_MODEL = "OpenVINO/Phi-3.5-mini-instruct-int4-ov"
DEFAULT_ZIM_ALIAS = "medicine.zim"
DEFAULT_ZIM_PROFILE = "nopic"
DEFAULT_T114_SYMLINK = Path("/dev/delphi-t114")
WIKIPEDIA_ZIM_INDEX_URL = "https://download.kiwix.org/zim/wikipedia/"
SUPPORTED_ZIM_PROFILES = ("maxi", "mini", "nopic")
ARCHIVE_PATTERNS = {
    profile: re.compile(rf"(wikipedia_en_medicine_{profile}_\d{{4}}-\d{{2}}\.zim)")
    for profile in SUPPORTED_ZIM_PROFILES
}


class BootstrapError(RuntimeError):
    """Raised when the Ubuntu/OpenVINO bootstrap cannot proceed."""


@dataclass(frozen=True)
class BootstrapPaths:
    root: Path
    venv_dir: Path
    config_dir: Path
    bin_dir: Path
    index_dir: Path
    library_dir: Path
    plaintext_dir: Path
    zim_dir: Path
    zim_releases_dir: Path
    models_dir: Path
    logs_dir: Path
    state_path: Path


@dataclass(frozen=True)
class ResolvedArchive:
    profile: str
    filename: str
    url: str
    alias: str = DEFAULT_ZIM_ALIAS


@dataclass(frozen=True)
class BootstrapState:
    archive_profile: str
    archive_filename: str
    archive_url: str
    archive_alias: str
    llm_model: str
    llm_base_url: str
    radio_device: str
    generated_at: str


def build_paths(root: Path) -> BootstrapPaths:
    root = root.expanduser().resolve()
    return BootstrapPaths(
        root=root,
        venv_dir=root / "venv",
        config_dir=root / "config",
        bin_dir=root / "bin",
        index_dir=root / "index",
        library_dir=root / "library",
        plaintext_dir=root / "library/plaintext",
        zim_dir=root / "library/zim",
        zim_releases_dir=root / "library/zim/releases",
        models_dir=root / "models",
        logs_dir=root / "logs",
        state_path=root / "bootstrap-state.json",
    )


def load_state(root: Path) -> BootstrapState | None:
    state_path = build_paths(root).state_path
    if not state_path.exists():
        return None

    raw = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise BootstrapError(f"Bootstrap state must be a JSON object: {state_path}")

    try:
        return BootstrapState(
            archive_profile=str(raw["archive_profile"]).strip(),
            archive_filename=str(raw["archive_filename"]).strip(),
            archive_url=str(raw["archive_url"]).strip(),
            archive_alias=str(raw.get("archive_alias", DEFAULT_ZIM_ALIAS)).strip()
            or DEFAULT_ZIM_ALIAS,
            llm_model=str(raw["llm_model"]).strip(),
            llm_base_url=str(raw["llm_base_url"]).strip(),
            radio_device=str(raw["radio_device"]).strip(),
            generated_at=str(raw["generated_at"]).strip(),
        )
    except KeyError as exc:
        raise BootstrapError(f"Bootstrap state is missing required field {exc.args[0]!r}") from exc


def select_latest_archive_filename(profile: str, directory_listing: str) -> str:
    pattern = ARCHIVE_PATTERNS.get(profile)
    if pattern is None:
        raise BootstrapError(
            f"Unsupported ZIM profile {profile!r}; expected one of {', '.join(SUPPORTED_ZIM_PROFILES)}"
        )

    matches = sorted(set(pattern.findall(directory_listing)))
    if not matches:
        raise BootstrapError(
            f"No archive matching profile {profile!r} was found at {WIKIPEDIA_ZIM_INDEX_URL}"
        )
    return matches[-1]


def resolve_archive(
    profile: str,
    *,
    root: Path | None = None,
    override_url: str | None = None,
    refresh: bool = False,
    urlopen_fn=request.urlopen,
) -> ResolvedArchive:
    profile = profile.strip().lower()
    if profile not in SUPPORTED_ZIM_PROFILES:
        raise BootstrapError(
            f"Unsupported ZIM profile {profile!r}; expected one of {', '.join(SUPPORTED_ZIM_PROFILES)}"
        )

    if override_url:
        filename = _archive_filename_from_url(override_url)
        return ResolvedArchive(profile=profile, filename=filename, url=override_url.strip())

    if root is not None and not refresh:
        state = load_state(root)
        if state is not None and state.archive_profile == profile:
            return ResolvedArchive(
                profile=state.archive_profile,
                filename=state.archive_filename,
                url=state.archive_url,
                alias=state.archive_alias,
            )

    with urlopen_fn(WIKIPEDIA_ZIM_INDEX_URL, timeout=30) as response:
        listing = response.read().decode("utf-8", errors="replace")
    filename = select_latest_archive_filename(profile, listing)
    return ResolvedArchive(profile=profile, filename=filename, url=WIKIPEDIA_ZIM_INDEX_URL + filename)


def detect_heltec_radio_device(
    requested_device: str,
    *,
    serial_root: Path = Path("/dev/serial/by-id"),
    stable_symlink: Path = DEFAULT_T114_SYMLINK,
) -> Path:
    requested_device = requested_device.strip()
    if requested_device and requested_device.lower() != "auto":
        return Path(requested_device).expanduser()

    candidates = sorted(
        path
        for path in serial_root.glob("*")
        if "heltec" in path.name.lower()
    )
    if len(candidates) == 1:
        return candidates[0]
    if stable_symlink.exists():
        return stable_symlink
    if not candidates:
        raise BootstrapError(
            (
                f"No Heltec serial device was found under {serial_root}, and {stable_symlink} "
                "is not present; rerun with --radio-device"
            )
        )
    raise BootstrapError(
        "Multiple Heltec serial devices were found; rerun with --radio-device to choose one: "
        + ", ".join(str(path) for path in candidates)
    )


def render_runtime_artifacts(
    root: Path,
    *,
    archive: ResolvedArchive,
    base_url: str,
    model: str,
    radio_device: Path,
) -> dict[str, str]:
    paths = build_paths(root)
    _ensure_runtime_directories(paths)

    sim_config_path = paths.config_dir / "oracle.ubuntu.ovms.sim.local.yaml"
    live_config_path = paths.config_dir / "oracle.ubuntu.ovms.live.local.yaml"
    sim_config_path.write_text(
        _config_text(
            node_name="delphi-42-ubuntu-ovms",
            radio_transport="simulated",
            radio_device="",
            base_url=base_url,
            model=model,
            index_path=paths.index_dir / "oracle-ubuntu-ovms.db",
            plaintext_dir=paths.plaintext_dir,
            zim_dir=paths.zim_dir,
            zim_alias=archive.alias,
        ),
        encoding="utf-8",
    )
    live_config_path.write_text(
        _config_text(
            node_name="delphi-42-ubuntu-ovms-live",
            radio_transport="meshtastic",
            radio_device=str(radio_device),
            base_url=base_url,
            model=model,
            index_path=paths.index_dir / "oracle-ubuntu-ovms.db",
            plaintext_dir=paths.plaintext_dir,
            zim_dir=paths.zim_dir,
            zim_alias=archive.alias,
        ),
        encoding="utf-8",
    )

    helper_paths = _write_helper_scripts(paths, sim_config_path, live_config_path)
    _write_state(paths, archive=archive, base_url=base_url, model=model, radio_device=radio_device)

    return {
        "root": str(paths.root),
        "venv_dir": str(paths.venv_dir),
        "sim_config_path": str(sim_config_path),
        "live_config_path": str(live_config_path),
        "state_path": str(paths.state_path),
        **helper_paths,
    }


def _archive_filename_from_url(url: str) -> str:
    parsed = urlparse(url.strip())
    filename = Path(parsed.path).name
    if not filename.endswith(".zim"):
        raise BootstrapError(f"Override URL must end with a .zim file name; got {url!r}")
    return filename


def _ensure_runtime_directories(paths: BootstrapPaths) -> None:
    for path in (
        paths.root,
        paths.config_dir,
        paths.bin_dir,
        paths.index_dir,
        paths.plaintext_dir,
        paths.zim_dir,
        paths.zim_releases_dir,
        paths.models_dir,
        paths.logs_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _write_state(
    paths: BootstrapPaths,
    *,
    archive: ResolvedArchive,
    base_url: str,
    model: str,
    radio_device: Path,
) -> None:
    state = BootstrapState(
        archive_profile=archive.profile,
        archive_filename=archive.filename,
        archive_url=archive.url,
        archive_alias=archive.alias,
        llm_model=model,
        llm_base_url=base_url,
        radio_device=str(radio_device),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    paths.state_path.write_text(
        json.dumps(state.__dict__, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_helper_scripts(
    paths: BootstrapPaths,
    sim_config_path: Path,
    live_config_path: Path,
) -> dict[str, str]:
    scripts = {
        "preflight_sim_path": paths.bin_dir / "preflight-sim",
        "preflight_live_path": paths.bin_dir / "preflight-live",
        "run_sim_path": paths.bin_dir / "run-sim",
        "run_live_path": paths.bin_dir / "run-live",
    }
    repo_root = REPO_ROOT
    python_path = paths.venv_dir / "bin/python"

    contents = {
        scripts["preflight_sim_path"]: textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd {json.dumps(str(repo_root))}
            exec {json.dumps(str(python_path))} -m scripts.host_preflight --config {json.dumps(str(sim_config_path))}
            """
        ),
        scripts["preflight_live_path"]: textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd {json.dumps(str(repo_root))}
            exec {json.dumps(str(python_path))} -m scripts.host_preflight --config {json.dumps(str(live_config_path))}
            """
        ),
        scripts["run_sim_path"]: textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd {json.dumps(str(repo_root))}
            exec env DELPHI_CONFIG={json.dumps(str(sim_config_path))} {json.dumps(str(python_path))} -m bot.dev_console
            """
        ),
        scripts["run_live_path"]: textwrap.dedent(
            f"""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd {json.dumps(str(repo_root))}
            exec env DELPHI_CONFIG={json.dumps(str(live_config_path))} {json.dumps(str(python_path))} -m bot.oracle_bot
            """
        ),
    }

    for path, body in contents.items():
        path.write_text(body, encoding="utf-8")
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return {name: str(path) for name, path in scripts.items()}


def _config_text(
    *,
    node_name: str,
    radio_transport: str,
    radio_device: str,
    base_url: str,
    model: str,
    index_path: Path,
    plaintext_dir: Path,
    zim_dir: Path,
    zim_alias: str,
) -> str:
    is_live_radio = radio_transport == "meshtastic"
    radio_spacing = 8.0 if is_live_radio else 0.0
    radio_retries = 2 if is_live_radio else 0
    radio_retry_delay = 15.0 if is_live_radio else 0.0
    radio_payload_bytes = 120 if is_live_radio else 0
    short_max_chars = 100 if is_live_radio else 120
    continuation_max_chars = 120 if is_live_radio else 600
    return textwrap.dedent(
        f"""\
        node_name: {node_name}

        radio:
          transport: {radio_transport}
          device: {_yaml_string(radio_device)}
          channel: 0
          text_packet_spacing_seconds: {radio_spacing}
          text_packet_retry_attempts: {radio_retries}
          text_packet_retry_delay_seconds: {radio_retry_delay}
          max_text_payload_bytes: {radio_payload_bytes}

        privacy:
          answer_public_messages: false
          share_position_publicly: false

        broadcasts:
          interval_minutes: 90
          messages:
            - THE ORACLE LISTENS. SEND DM FOR COUNSEL.
            - ASH NODE AWAKE.
            - SEEK WISDOM IN PRIVATE.

        knowledge:
          plaintext_dir: {_yaml_string(str(plaintext_dir))}
          index_path: {_yaml_string(str(index_path))}
          kiwix_url: http://127.0.0.1:8080
          zim_dir: {_yaml_string(str(zim_dir))}
          runtime_zim_fallback_enabled: true
          runtime_zim_allowlist:
            - {zim_alias}
          runtime_zim_search_limit: 3

        llm:
          backend: openai-compatible
          provider: ovms
          base_url: {_yaml_string(base_url)}
          model: {_yaml_string(model)}
          api_key: sk-
          timeout_seconds: 45

        reply:
          short_max_chars: {short_max_chars}
          continuation_max_chars: {continuation_max_chars}
          max_continuation_packets: 3

        wifi:
          ssid: DELPHI-42-OVMS
        """
    )


def _yaml_string(value: str) -> str:
    return json.dumps(value)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve and render local runtime artifacts for the Ubuntu/OpenVINO bootstrap."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve-zim", help="Resolve the selected ZIM archive.")
    resolve_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    resolve_parser.add_argument(
        "--profile",
        choices=SUPPORTED_ZIM_PROFILES,
        default=DEFAULT_ZIM_PROFILE,
    )
    resolve_parser.add_argument("--zim-url", help="Explicit ZIM URL override.", default="")
    resolve_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore any pinned bootstrap state and resolve the archive again.",
    )

    detect_parser = subparsers.add_parser("detect-radio", help="Detect the live Heltec radio path.")
    detect_parser.add_argument("--radio-device", default="auto")
    detect_parser.add_argument("--serial-root", type=Path, default=Path("/dev/serial/by-id"))
    detect_parser.add_argument("--stable-symlink", type=Path, default=DEFAULT_T114_SYMLINK)

    render_parser = subparsers.add_parser(
        "render-runtime",
        help="Write bootstrap state, generated configs, and helper commands.",
    )
    render_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    render_parser.add_argument(
        "--archive-profile",
        choices=SUPPORTED_ZIM_PROFILES,
        required=True,
    )
    render_parser.add_argument("--archive-filename", required=True)
    render_parser.add_argument("--archive-url", required=True)
    render_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    render_parser.add_argument("--model", default=DEFAULT_MODEL)
    render_parser.add_argument("--radio-device", required=True)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        if args.command == "resolve-zim":
            archive = resolve_archive(
                args.profile,
                root=args.root,
                override_url=args.zim_url or None,
                refresh=bool(args.refresh),
            )
            print(json.dumps(archive.__dict__, indent=2, sort_keys=True))
            return

        if args.command == "detect-radio":
            radio_path = detect_heltec_radio_device(
                args.radio_device,
                serial_root=args.serial_root,
                stable_symlink=args.stable_symlink,
            )
            print(json.dumps({"radio_device": str(radio_path)}, indent=2, sort_keys=True))
            return

        if args.command == "render-runtime":
            archive = ResolvedArchive(
                profile=args.archive_profile,
                filename=args.archive_filename,
                url=args.archive_url,
            )
            radio_device = Path(args.radio_device).expanduser()
            payload = render_runtime_artifacts(
                args.root,
                archive=archive,
                base_url=args.base_url,
                model=args.model,
                radio_device=radio_device,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
    except BootstrapError as exc:
        raise SystemExit(str(exc)) from exc

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
