from __future__ import annotations

from pathlib import Path

from scripts.host_preflight import run_preflight


class ReadyRunner:
    def __init__(self, **_: object) -> None:
        pass

    def complete(self, prompt: str, *, system_prompt: str | None = None, temperature: float = 0.0) -> str:
        return "ready"


def test_run_preflight_checks_kiwix_and_mesh_settings(tmp_path: Path) -> None:
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)
    (zim_dir / "medicine.zim").write_bytes(b"zim")

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  zim_dir: {zim_dir}
  zim_allowlist:
    - medicine.zim
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=lambda name: object(),
        runner_factory=ReadyRunner,
    )

    assert any(result.name == "llm_tools_kiwix" and result.ok for result in results)
    assert any(result.name == "zim-files" and result.ok for result in results)
    assert any(result.name == "mesh-packets" and result.ok for result in results)


def test_run_preflight_flags_missing_allowlisted_archive(tmp_path: Path) -> None:
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  zim_dir: {zim_dir}
  zim_allowlist:
    - medicine.zim
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=lambda name: object(),
        runner_factory=ReadyRunner,
    )

    zim_check = next(result for result in results if result.name == "zim-files")
    assert zim_check.ok is False
    assert "medicine.zim" in zim_check.details
