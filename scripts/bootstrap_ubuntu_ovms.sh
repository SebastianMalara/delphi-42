#!/usr/bin/env bash
set -euo pipefail

ROOT=""
ZIM_PROFILE="nopic"
ZIM_URL=""
RADIO_DEVICE="auto"
REFRESH_ZIM=0
LIVE_RELOGIN_REQUIRED=0

MODEL_ID="OpenVINO/Phi-3.5-mini-instruct-int4-ov"
OVMS_BASE_URL="http://127.0.0.1:8000/v3"
OVMS_IMAGE="openvino/model_server:latest-gpu"
OVMS_CONTAINER="delphi-ovms"
UDEV_RULE_PATH="/etc/udev/rules.d/99-delphi-t114.rules"
STABLE_T114_PATH="/dev/delphi-t114"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELPER="$REPO_ROOT/scripts/bootstrap_ubuntu_ovms.py"

if [[ -z "$ROOT" ]]; then
  ROOT="$REPO_ROOT/artifacts/ubuntu-ovms"
fi

status() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap_ubuntu_ovms.sh [options]

Options:
  --root PATH             Runtime root for the gitignored bootstrap output.
  --zim-profile PROFILE   One of: nopic, maxi, mini. Default: nopic.
  --zim-url URL           Override the Kiwix download URL.
  --radio-device PATH     Explicit radio path, or "auto" to detect Heltec by-id path.
  --refresh-zim           Ignore pinned state and resolve/download the ZIM again.
  --help                  Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT="$2"
      shift 2
      ;;
    --zim-profile)
      ZIM_PROFILE="$2"
      shift 2
      ;;
    --zim-url)
      ZIM_URL="$2"
      shift 2
      ;;
    --radio-device)
      RADIO_DEVICE="$2"
      shift 2
      ;;
    --refresh-zim)
      REFRESH_ZIM=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

ROOT_ABS="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "$ROOT")"
VENV_DIR="$ROOT_ABS/venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

require_gpu() {
  if ! compgen -G "/dev/dri/render*" >/dev/null; then
    echo "No /dev/dri/render* device is available; this bootstrap is scoped to the Ubuntu/OpenVINO GPU host lane." >&2
    exit 1
  fi
}

install_host_packages() {
  sudo apt-get update
  sudo apt-get install -y \
    python3-venv \
    python3-pip \
    libzim-dev \
    docker.io \
    curl \
    ca-certificates
}

ensure_plugdev_membership() {
  if ! getent group plugdev >/dev/null; then
    echo "The plugdev group is missing on this host; create it before running the live T114 path." >&2
    exit 1
  fi

  if id -nG "$USER" | tr ' ' '\n' | grep -Fx plugdev >/dev/null; then
    return
  fi

  sudo usermod -aG plugdev "$USER"
  LIVE_RELOGIN_REQUIRED=1
  echo "Added $USER to plugdev. This run will complete host and simulated setup, but live T114 preflight will be skipped until you log out and back in." >&2
}

install_t114_udev_rule() {
  local rule='SUBSYSTEM=="tty", ATTRS{idVendor}=="239a", ATTRS{idProduct}=="4405", GROUP="plugdev", MODE="0660", SYMLINK+="delphi-t114"'
  printf '%s\n' "$rule" | sudo tee "$UDEV_RULE_PATH" >/dev/null
  sudo udevadm control --reload-rules
  sudo udevadm trigger --subsystem-match=tty
}

create_python_env() {
  status "Preparing Python virtual environment under $VENV_DIR"
  mkdir -p "$ROOT_ABS"
  local recreate_venv=0
  if [[ -x "$PIP_BIN" ]]; then
    local pip_shebang pip_python
    pip_shebang="$(head -n 1 "$PIP_BIN" || true)"
    if [[ "$pip_shebang" == '#!'* ]]; then
      pip_python="${pip_shebang#\#!}"
      if [[ ! -x "$pip_python" ]]; then
        status "Existing virtual environment references missing interpreter $pip_python; recreating it under $VENV_DIR"
        recreate_venv=1
      fi
    fi
  fi

  if [[ "$recreate_venv" -eq 1 ]]; then
    rm -rf "$VENV_DIR"
  fi

  if [[ ! -x "$PYTHON_BIN" ]]; then
    status "Creating virtual environment"
    python3 -m venv "$VENV_DIR"
  fi

  status "Upgrading pip/setuptools/wheel"
  "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel
  (
    cd "$REPO_ROOT"
    status "Installing Delphi-42 package in editable mode"
    "$PYTHON_BIN" -m pip install -e '.[bot,llm,zim]'
  )
}

resolve_archive() {
  local args=("$HELPER" "resolve-zim" "--root" "$ROOT_ABS" "--profile" "$ZIM_PROFILE")
  if [[ -n "$ZIM_URL" ]]; then
    args+=("--zim-url" "$ZIM_URL")
  fi
  if [[ "$REFRESH_ZIM" -eq 1 ]]; then
    args+=("--refresh")
  fi
  python3 "${args[@]}"
}

json_field() {
  local field="$1"
  python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$field"
}

download_archive() {
  local archive_url="$1"
  local archive_filename="$2"

  mkdir -p "$ROOT_ABS/library/zim/releases"
  local target="$ROOT_ABS/library/zim/releases/$archive_filename"
  local temp_target="${target}.part"

  if [[ ! -f "$target" || "$REFRESH_ZIM" -eq 1 ]]; then
    status "Downloading ZIM archive: $archive_filename"
    rm -f "$temp_target"
    curl --fail --location --continue-at - --output "$temp_target" "$archive_url"
    mv "$temp_target" "$target"
  else
    status "Reusing existing ZIM archive: $archive_filename"
  fi

  mkdir -p "$ROOT_ABS/library/zim"
  ln -sfn "releases/$archive_filename" "$ROOT_ABS/library/zim/medicine.zim"
}

seed_and_build_index() {
  status "Seeding plaintext corpus from sample_data/plaintext"
  mkdir -p "$ROOT_ABS/library/plaintext/bootstrap-seed"
  cp -R "$REPO_ROOT/sample_data/plaintext/." "$ROOT_ABS/library/plaintext/bootstrap-seed/"

  (
    cd "$REPO_ROOT"
    status "Extracting ZIM contents into $ROOT_ABS/library/plaintext"
    "$PYTHON_BIN" -m ingest.extract_zim \
      --zim-dir "$ROOT_ABS/library/zim" \
      --output-dir "$ROOT_ABS/library/plaintext" \
      --allowlist "medicine.zim"
    status "Building retrieval index at $ROOT_ABS/index/oracle-ubuntu-ovms.db"
    "$PYTHON_BIN" -m ingest.build_index \
      --input-dir "$ROOT_ABS/library/plaintext" \
      --db "$ROOT_ABS/index/oracle-ubuntu-ovms.db"
  )
}

detect_radio() {
  python3 "$HELPER" detect-radio --radio-device "$RADIO_DEVICE" --stable-symlink "$STABLE_T114_PATH"
}

ensure_docker_service() {
  status "Ensuring Docker service is enabled"
  sudo systemctl enable --now docker
}

restart_ovms_container() {
  status "Starting OVMS container $OVMS_CONTAINER with model $MODEL_ID"
  local render_gid
  render_gid="$(stat -c '%g' /dev/dri/render* | head -n 1)"
  mkdir -p "$ROOT_ABS/models"

  sudo docker rm -f "$OVMS_CONTAINER" >/dev/null 2>&1 || true
  sudo docker run \
    --user "$(id -u):$(id -g)" \
    -d \
    --device /dev/dri \
    --group-add="$render_gid" \
    --name "$OVMS_CONTAINER" \
    --restart unless-stopped \
    -p 8000:8000 \
    -v "$ROOT_ABS/models:/models:rw" \
    "$OVMS_IMAGE" \
    --source_model "$MODEL_ID" \
    --model_repository_path models \
    --task text_generation \
    --rest_port 8000 \
    --target_device GPU \
    --cache_size 2 >/dev/null
}

wait_for_ovms() {
  status "Waiting for OVMS to expose model metadata on $OVMS_BASE_URL/models"
  local attempt
  for attempt in $(seq 1 90); do
    status "OVMS readiness check $attempt/90"
    if curl --silent --fail "$OVMS_BASE_URL/models" | python3 -c '
import json
import sys

payload = json.load(sys.stdin)
target = sys.argv[1]
ids = [str(item.get("id", "")).strip() for item in payload.get("data", [])]
raise SystemExit(0 if target in ids else 1)
' "$MODEL_ID"
    then
      return
    fi
    sleep 5
  done

  echo "OVMS did not expose $MODEL_ID on $OVMS_BASE_URL/models in time." >&2
  sudo docker logs --tail 200 "$OVMS_CONTAINER" >&2 || true
  exit 1
}

render_runtime_artifacts() {
  local archive_profile="$1"
  local archive_filename="$2"
  local archive_url="$3"
  local radio_device="$4"
  status "Rendering runtime wrappers and local configs"
  python3 "$HELPER" render-runtime \
    --root "$ROOT_ABS" \
    --archive-profile "$archive_profile" \
    --archive-filename "$archive_filename" \
    --archive-url "$archive_url" \
    --base-url "$OVMS_BASE_URL" \
    --model "$MODEL_ID" \
    --radio-device "$radio_device"
}

main() {
  status "Bootstrap starting with runtime root $ROOT_ABS"
  require_gpu
  status "GPU device check passed"
  install_host_packages
  ensure_plugdev_membership
  install_t114_udev_rule

  local radio_json radio_device
  status "Detecting radio device"
  radio_json="$(detect_radio)"
  radio_device="$(printf '%s' "$radio_json" | json_field radio_device)"
  status "Using radio device: $radio_device"

  create_python_env

  local archive_json
  status "Resolving ZIM archive metadata for profile $ZIM_PROFILE"
  archive_json="$(resolve_archive)"
  local archive_profile archive_filename archive_url archive_alias
  archive_profile="$(printf '%s' "$archive_json" | json_field profile)"
  archive_filename="$(printf '%s' "$archive_json" | json_field filename)"
  archive_url="$(printf '%s' "$archive_json" | json_field url)"
  archive_alias="$(printf '%s' "$archive_json" | json_field alias)"

  if [[ "$archive_alias" != "medicine.zim" ]]; then
    echo "Unexpected archive alias from helper: $archive_alias" >&2
    exit 1
  fi

  download_archive "$archive_url" "$archive_filename"
  seed_and_build_index

  ensure_docker_service
  restart_ovms_container
  wait_for_ovms

  render_runtime_artifacts "$archive_profile" "$archive_filename" "$archive_url" "$radio_device" >/dev/null

  status "Running simulated preflight"
  "$ROOT_ABS/bin/preflight-sim"
  if [[ "$LIVE_RELOGIN_REQUIRED" -eq 0 ]]; then
    status "Running live preflight"
    "$ROOT_ABS/bin/preflight-live"
  else
    echo "Skipping live preflight for this run because plugdev group membership was just granted. Log out and back in, then rerun the bootstrap or run $ROOT_ABS/bin/preflight-live." >&2
  fi

  cat <<EOF
Bootstrap complete.

Runtime root: $ROOT_ABS
ZIM release: $archive_filename
Live radio: $radio_device

Run the simulated console with:
  $ROOT_ABS/bin/run-sim

Run the live bot with:
  $ROOT_ABS/bin/run-live
EOF
}

main "$@"
