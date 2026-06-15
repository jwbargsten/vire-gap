#!/usr/bin/env bash
# Install the per-user launchd agents (no root):
#   - org.bargsten.copilot-tinyproxy : keeps tinyproxy running (KeepAlive)
#   - org.bargsten.copilot-usage     : runs `copilot-usage usage` every 60s
#
# Idempotent: re-run after code changes to reload. Uninstall with:
#   launchctl unload ~/Library/LaunchAgents/org.bargsten.copilot-{tinyproxy,usage}.plist
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DENY_DIR="$HOME/.copilot-deny"
STATE_DIR="$HOME/.copilot_budget"
AGENTS="$HOME/Library/LaunchAgents"
mkdir -p "$DENY_DIR" "$STATE_DIR" "$AGENTS"

# tinyproxy needs its config and a filter file present before it starts.
cp "$REPO/tinyproxy.conf" "$DENY_DIR/tinyproxy.conf"
[ -f "$DENY_DIR/filter" ] || : > "$DENY_DIR/filter"   # empty filter = nothing blocked

# Make sure the `copilot-usage` console script exists, then resolve its path.
uv tool install --editable "$REPO"
CU="$(command -v copilot-usage || true)"
[ -x "$CU" ] || CU="$HOME/.local/bin/copilot-usage"
if [ ! -x "$CU" ]; then
    echo "could not find the copilot-usage executable after install" >&2
    exit 1
fi
echo "using copilot-usage at: $CU"

install_agent() {
    local name="$1"; shift
    local src="$REPO/launchd/$name.plist"
    local dst="$AGENTS/$name.plist"
    sed -e "s#__HOME__#$HOME#g" -e "s#__COPILOT_USAGE__#$CU#g" "$src" > "$dst"
    launchctl unload "$dst" 2>/dev/null || true
    launchctl load "$dst"
    echo "loaded $name"
}

install_agent org.bargsten.copilot-tinyproxy
install_agent org.bargsten.copilot-usage

echo "done. check with: launchctl list | grep copilot"
echo "logs: $STATE_DIR/usage.{out,err}.log  and  $DENY_DIR/tinyproxy.{out,err}.log"
