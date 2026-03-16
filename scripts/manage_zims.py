from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from urllib import request
from urllib.parse import urlparse


DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "artifacts/ubuntu-ovms"
DEFAULT_ZIMIT_IMAGE = "ghcr.io/openzim/zimit:latest"
DEFAULT_MEDICINE_PROFILE = "nopic"
SUPPORTED_MEDICINE_PROFILES = ("maxi", "mini", "nopic")
DEFAULT_BUNDLE = "core-survival"


@dataclass(frozen=True)
class CatalogArchive:
    alias: str
    kind: str
    source_url: str
    filename: str
    browse_enabled: bool
    answer_enabled: bool
    created_at: str
    notes: str = ""


@dataclass(frozen=True)
class CatalogSource:
    alias: str
    index_url: str
    pattern_template: str
    answer_enabled: bool = True
    notes: str = ""


CATALOG_SOURCES = {
    "medicine.zim": CatalogSource(
        alias="medicine.zim",
        index_url="https://download.kiwix.org/zim/wikipedia/",
        pattern_template=r"(wikipedia_en_medicine_{profile}_\d{{4}}-\d{{2}}\.zim)",
        answer_enabled=True,
        notes="Wikipedia medicine curated archive.",
    ),
    "mdwiki.zim": CatalogSource(
        alias="mdwiki.zim",
        index_url="https://download.kiwix.org/zim/other/",
        pattern_template=r"(mdwiki_en_all_maxi_\d{{4}}-\d{{2}}\.zim)",
        answer_enabled=True,
        notes="Medical reference encyclopedia.",
    ),
    "ifixit.zim": CatalogSource(
        alias="ifixit.zim",
        index_url="https://download.kiwix.org/zim/ifixit/",
        pattern_template=r"(ifixit_en_all_\d{{4}}-\d{{2}}\.zim)",
        answer_enabled=True,
        notes="Repair and teardown manuals.",
    ),
    "appropedia.zim": CatalogSource(
        alias="appropedia.zim",
        index_url="https://download.kiwix.org/zim/other/",
        pattern_template=r"(appropedia_en_all_maxi_\d{{4}}-\d{{2}}\.zim)",
        answer_enabled=True,
        notes="Appropriate technology and rebuild knowledge.",
    ),
    "wikivoyage.zim": CatalogSource(
        alias="wikivoyage.zim",
        index_url="https://download.kiwix.org/zim/wikivoyage/",
        pattern_template=r"(wikivoyage_en_all_nopic_\d{{4}}-\d{{2}}\.zim)",
        answer_enabled=True,
        notes="Logistics and place knowledge.",
    ),
}

CORE_SURVIVAL_BUNDLE = (
    "medicine.zim",
    "mdwiki.zim",
    "ifixit.zim",
    "appropedia.zim",
    "wikivoyage.zim",
)


class ManagedZimError(RuntimeError):
    """Raised when managed ZIM operations fail."""


def registry_path(root: Path) -> Path:
    return root.expanduser().resolve() / "library/zim/managed-archives.json"


def releases_dir(root: Path) -> Path:
    return root.expanduser().resolve() / "library/zim/releases"


def aliases_dir(root: Path) -> Path:
    return root.expanduser().resolve() / "library/zim"


def load_registry(root: Path) -> list[CatalogArchive]:
    path = registry_path(root)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ManagedZimError(f"Managed archive registry must be a list: {path}")
    return [CatalogArchive(**item) for item in raw]


def save_registry(root: Path, archives: Sequence[CatalogArchive]) -> None:
    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(item) for item in archives], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def answer_enabled_aliases(root: Path) -> tuple[str, ...]:
    return tuple(item.alias for item in load_registry(root) if item.answer_enabled)


def list_archives(root: Path) -> dict[str, object]:
    archives = load_registry(root)
    return {
        "root": str(root.expanduser().resolve()),
        "archives": [asdict(item) for item in archives],
        "answer_enabled_aliases": [item.alias for item in archives if item.answer_enabled],
    }


def ensure_core_survival_bundle(
    root: Path,
    *,
    medicine_profile: str = DEFAULT_MEDICINE_PROFILE,
    medicine_url_override: str | None = None,
    refresh: bool = False,
    urlopen_fn=request.urlopen,
) -> dict[str, object]:
    root = root.expanduser().resolve()
    existing = {item.alias: item for item in load_registry(root)}
    updated = dict(existing)

    for alias in CORE_SURVIVAL_BUNDLE:
        source = CATALOG_SOURCES[alias]
        resolved = resolve_catalog_archive(
            alias,
            medicine_profile=medicine_profile,
            medicine_url_override=medicine_url_override,
            refresh=refresh,
            urlopen_fn=urlopen_fn,
        )
        staged = stage_downloaded_archive(
            root,
            alias=alias,
            url=resolved["url"],
            filename=resolved["filename"],
            answer_enabled=source.answer_enabled,
            notes=source.notes,
            refresh=refresh,
            urlopen_fn=urlopen_fn,
        )
        updated[alias] = staged

    ordered = [updated[alias] for alias in CORE_SURVIVAL_BUNDLE]
    for alias, archive in sorted(updated.items()):
        if alias in CORE_SURVIVAL_BUNDLE:
            continue
        ordered.append(archive)
    save_registry(root, ordered)

    primary = updated["medicine.zim"]
    return {
        "root": str(root),
        "archives": [asdict(item) for item in ordered],
        "answer_enabled_aliases": [item.alias for item in ordered if item.answer_enabled],
        "primary_archive": {
            "alias": primary.alias,
            "filename": primary.filename,
            "url": primary.source_url,
            "profile": medicine_profile,
        },
    }


def resolve_catalog_archive(
    alias: str,
    *,
    medicine_profile: str,
    medicine_url_override: str | None,
    refresh: bool,
    urlopen_fn=request.urlopen,
) -> dict[str, str]:
    if alias not in CATALOG_SOURCES:
        raise ManagedZimError(f"Unsupported catalog alias: {alias}")
    source = CATALOG_SOURCES[alias]

    if alias == "medicine.zim" and medicine_url_override:
        filename = filename_from_url(medicine_url_override)
        return {"alias": alias, "filename": filename, "url": medicine_url_override}

    profile = medicine_profile if alias == "medicine.zim" else ""
    pattern = source.pattern_template.format(profile=profile)
    with urlopen_fn(source.index_url, timeout=30) as response:
        listing = response.read().decode("utf-8", errors="replace")
    matches = sorted(set(re.findall(pattern, listing)))
    if not matches:
        raise ManagedZimError(f"No archive found for alias {alias} at {source.index_url}")
    filename = matches[-1]
    return {"alias": alias, "filename": filename, "url": source.index_url + filename}


def stage_downloaded_archive(
    root: Path,
    *,
    alias: str,
    url: str,
    filename: str,
    answer_enabled: bool,
    notes: str,
    refresh: bool = False,
    browse_enabled: bool = True,
    urlopen_fn=request.urlopen,
) -> CatalogArchive:
    release_root = releases_dir(root)
    alias_root = aliases_dir(root)
    release_root.mkdir(parents=True, exist_ok=True)
    alias_root.mkdir(parents=True, exist_ok=True)

    target = release_root / filename
    if refresh and target.exists():
        target.unlink()
    if not target.exists():
        download_to_path(url, target, urlopen_fn=urlopen_fn)

    alias_path = alias_root / alias
    if alias_path.exists() or alias_path.is_symlink():
        alias_path.unlink()
    alias_path.symlink_to(Path("releases") / filename)
    return CatalogArchive(
        alias=alias,
        kind="catalog",
        source_url=url,
        filename=filename,
        browse_enabled=browse_enabled,
        answer_enabled=answer_enabled,
        created_at=datetime.now(timezone.utc).isoformat(),
        notes=notes,
    )


def add_url_archive(
    root: Path,
    *,
    alias: str,
    url: str,
    answer_enabled: bool,
    urlopen_fn=request.urlopen,
) -> CatalogArchive:
    filename = filename_from_url(url)
    archive = stage_downloaded_archive(
        root,
        alias=alias,
        url=url,
        filename=filename,
        answer_enabled=answer_enabled,
        notes="Operator-managed direct URL import.",
        urlopen_fn=urlopen_fn,
    )
    _upsert_archive(root, archive)
    return archive


def add_file_archive(
    root: Path,
    *,
    alias: str,
    source_path: Path,
    answer_enabled: bool,
) -> CatalogArchive:
    source_path = source_path.expanduser().resolve()
    if not source_path.exists():
        raise ManagedZimError(f"Local ZIM file does not exist: {source_path}")
    if source_path.suffix != ".zim":
        raise ManagedZimError(f"Local path must be a .zim file: {source_path}")

    release_root = releases_dir(root)
    alias_root = aliases_dir(root)
    release_root.mkdir(parents=True, exist_ok=True)
    alias_root.mkdir(parents=True, exist_ok=True)
    target = release_root / source_path.name
    shutil.copy2(source_path, target)
    alias_path = alias_root / alias
    if alias_path.exists() or alias_path.is_symlink():
        alias_path.unlink()
    alias_path.symlink_to(Path("releases") / source_path.name)

    archive = CatalogArchive(
        alias=alias,
        kind="file",
        source_url=str(source_path),
        filename=source_path.name,
        browse_enabled=True,
        answer_enabled=answer_enabled,
        created_at=datetime.now(timezone.utc).isoformat(),
        notes="Operator-managed local file import.",
    )
    _upsert_archive(root, archive)
    return archive


def add_zimit_archive(
    root: Path,
    *,
    alias: str,
    website_url: str,
    answer_enabled: bool,
    zimit_image: str = DEFAULT_ZIMIT_IMAGE,
) -> CatalogArchive:
    release_root = releases_dir(root)
    release_root.mkdir(parents=True, exist_ok=True)
    archive_stem = Path(alias).stem or alias
    output_root = release_root / f"{archive_stem}.zimit"
    output_root.mkdir(parents=True, exist_ok=True)

    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{output_root}:/output",
        "-w",
        "/output",
        zimit_image,
        "zimit",
        "--seeds",
        website_url,
        "--name",
        archive_stem,
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        raise ManagedZimError(f"zimit failed for {website_url}") from exc

    produced = sorted(output_root.glob("*.zim"))
    if not produced:
        raise ManagedZimError(f"zimit did not produce a .zim file in {output_root}")

    generated = produced[-1]
    final_target = release_root / generated.name
    shutil.move(str(generated), final_target)
    shutil.rmtree(output_root, ignore_errors=True)
    alias_path = aliases_dir(root) / alias
    aliases_dir(root).mkdir(parents=True, exist_ok=True)
    if alias_path.exists() or alias_path.is_symlink():
        alias_path.unlink()
    alias_path.symlink_to(Path("releases") / final_target.name)

    archive = CatalogArchive(
        alias=alias,
        kind="zimit",
        source_url=website_url,
        filename=final_target.name,
        browse_enabled=True,
        answer_enabled=answer_enabled,
        created_at=datetime.now(timezone.utc).isoformat(),
        notes="Website-to-ZIM import via openzim/zimit.",
    )
    _upsert_archive(root, archive)
    return archive


def set_answer_enabled(root: Path, *, alias: str, enabled: bool) -> CatalogArchive:
    archives = load_registry(root)
    updated: list[CatalogArchive] = []
    selected: CatalogArchive | None = None
    for item in archives:
        if item.alias != alias:
            updated.append(item)
            continue
        selected = CatalogArchive(
            alias=item.alias,
            kind=item.kind,
            source_url=item.source_url,
            filename=item.filename,
            browse_enabled=item.browse_enabled,
            answer_enabled=enabled,
            created_at=item.created_at,
            notes=item.notes,
        )
        updated.append(selected)
    if selected is None:
        raise ManagedZimError(f"Unknown alias in registry: {alias}")
    save_registry(root, updated)
    return selected


def sync_allowlist(root: Path) -> dict[str, object]:
    root = root.expanduser().resolve()
    if __package__ in {None, ""}:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from scripts.bootstrap_ubuntu_ovms import (  # type: ignore
            ResolvedArchive,
            build_paths,
            load_state,
            render_runtime_artifacts,
        )
    else:
        from scripts.bootstrap_ubuntu_ovms import (
            ResolvedArchive,
            build_paths,
            load_state,
            render_runtime_artifacts,
        )

    state = load_state(root)
    if state is None:
        raise ManagedZimError(
            f"Bootstrap state is missing under {build_paths(root).state_path}; run the bootstrap once first."
        )

    archive = ResolvedArchive(
        profile=state.archive_profile,
        filename=state.archive_filename,
        url=state.archive_url,
        alias=state.archive_alias,
    )
    rendered = render_runtime_artifacts(
        root,
        archive=archive,
        base_url=state.llm_base_url,
        kiwix_url=state.kiwix_url,
        model=state.llm_model,
        radio_device=Path(state.radio_device).expanduser(),
    )
    return {
        "root": str(root),
        "answer_enabled_aliases": list(answer_enabled_aliases(root)),
        "rendered": rendered,
    }


def filename_from_url(url: str) -> str:
    parsed = urlparse(url.strip())
    filename = Path(parsed.path).name
    if not filename.endswith(".zim"):
        raise ManagedZimError(f"URL must point to a .zim file: {url}")
    return filename


def download_to_path(url: str, path: Path, *, urlopen_fn=request.urlopen) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".part")
    with urlopen_fn(url, timeout=60) as response, temp_path.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    temp_path.replace(path)


def _upsert_archive(root: Path, archive: CatalogArchive) -> None:
    archives = load_registry(root)
    updated: list[CatalogArchive] = [item for item in archives if item.alias != archive.alias]
    updated.append(archive)
    updated.sort(key=lambda item: item.alias)
    save_registry(root, updated)


def _bool_flag(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got {value!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage local staged ZIM archives for Delphi-42.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List managed archives.")
    list_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    ensure_parser = subparsers.add_parser("ensure-bundle", help="Ensure the default survival bundle is staged.")
    ensure_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ensure_parser.add_argument("--bundle", default=DEFAULT_BUNDLE)
    ensure_parser.add_argument("--profile", choices=SUPPORTED_MEDICINE_PROFILES, default=DEFAULT_MEDICINE_PROFILE)
    ensure_parser.add_argument("--zim-url", default="")
    ensure_parser.add_argument("--refresh", action="store_true")

    add_url_parser = subparsers.add_parser("add-url", help="Download a public ZIM by URL and register it.")
    add_url_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    add_url_parser.add_argument("--alias", required=True)
    add_url_parser.add_argument("--url", required=True)
    add_url_parser.add_argument("--answer-enabled", action="store_true")

    add_file_parser = subparsers.add_parser("add-file", help="Copy a local ZIM file into the managed runtime.")
    add_file_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    add_file_parser.add_argument("--alias", required=True)
    add_file_parser.add_argument("--path", type=Path, required=True)
    add_file_parser.add_argument("--answer-enabled", action="store_true")

    add_zimit_parser = subparsers.add_parser("add-zimit", help="Build a website ZIM through openzim/zimit.")
    add_zimit_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    add_zimit_parser.add_argument("--alias", required=True)
    add_zimit_parser.add_argument("--url", required=True)
    add_zimit_parser.add_argument("--answer-enabled", action="store_true")
    add_zimit_parser.add_argument("--zimit-image", default=DEFAULT_ZIMIT_IMAGE)

    set_answer_parser = subparsers.add_parser("set-answer", help="Enable or disable answer-time retrieval for an alias.")
    set_answer_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    set_answer_parser.add_argument("--alias", required=True)
    set_answer_parser.add_argument("--enabled", required=True, type=_bool_flag)

    sync_parser = subparsers.add_parser(
        "sync-allowlist",
        help="Rewrite generated runtime configs from the current answer-enabled registry state.",
    )
    sync_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "list":
            print(json.dumps(list_archives(args.root), indent=2, sort_keys=True))
            return
        if args.command == "ensure-bundle":
            if args.bundle != DEFAULT_BUNDLE:
                raise ManagedZimError(f"Unsupported bundle {args.bundle!r}")
            payload = ensure_core_survival_bundle(
                args.root,
                medicine_profile=args.profile,
                medicine_url_override=args.zim_url or None,
                refresh=bool(args.refresh),
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        if args.command == "add-url":
            archive = add_url_archive(
                args.root,
                alias=args.alias,
                url=args.url,
                answer_enabled=bool(args.answer_enabled),
            )
            print(json.dumps(asdict(archive), indent=2, sort_keys=True))
            return
        if args.command == "add-file":
            archive = add_file_archive(
                args.root,
                alias=args.alias,
                source_path=args.path,
                answer_enabled=bool(args.answer_enabled),
            )
            print(json.dumps(asdict(archive), indent=2, sort_keys=True))
            return
        if args.command == "add-zimit":
            archive = add_zimit_archive(
                args.root,
                alias=args.alias,
                website_url=args.url,
                answer_enabled=bool(args.answer_enabled),
                zimit_image=args.zimit_image,
            )
            print(json.dumps(asdict(archive), indent=2, sort_keys=True))
            return
        if args.command == "set-answer":
            archive = set_answer_enabled(
                args.root,
                alias=args.alias,
                enabled=bool(args.enabled),
            )
            print(json.dumps(asdict(archive), indent=2, sort_keys=True))
            return
        if args.command == "sync-allowlist":
            print(json.dumps(sync_allowlist(args.root), indent=2, sort_keys=True))
            return
    except ManagedZimError as exc:
        raise SystemExit(str(exc)) from exc

    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
