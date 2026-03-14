from pathlib import Path

from scripts.host_preflight import CheckResult, run_preflight
from scripts.host_preflight import main as _host_preflight_main


def main() -> None:
    _host_preflight_main(default_config=Path("config/oracle.mac.sim.yaml"), banner_label="mac")


if __name__ == "__main__":
    main()
