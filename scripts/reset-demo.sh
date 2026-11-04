#!/usr/bin/env bash
# Reset this repo to its pre-depot state so the "make it depot-ready" walkthrough can be run again.
#
#   1. Removes the demo from Demo Depot (tears down running instances, deletes versions, images, media).
#   2. Deletes the v* git tags locally and on origin, so v0.1.0 can be published again.
#   3. Deletes the depot artifacts from the working tree (demo.yaml, DEMO.md, ld/, media/, publish workflow).
#
# The app itself (web/, including its Dockerfile) and README.md are left alone.
#
# Usage: scripts/reset-demo.sh [--yes] [--dry-run] [--skip-depot] [--skip-tags] [--skip-files] [--slug <slug>]
#
# Depot access uses the personal token saved by `ddu auth login` (~/.config/demo-depot/config.json),
# or DD_TOKEN / DD_URL from the environment.
set -euo pipefail

YES=0 DRY=0 DO_DEPOT=1 DO_TAGS=1 DO_FILES=1 SLUG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y) YES=1 ;;
    --dry-run) DRY=1 ;;
    --skip-depot) DO_DEPOT=0 ;;
    --skip-tags) DO_TAGS=0 ;;
    --skip-files) DO_FILES=0 ;;
    --slug) SLUG="$2"; shift ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Everything the depot skill adds on top of the app. Edit this list if the layout changes.
ARTIFACTS=(demo.yaml DEMO.md ld media .github/workflows/publish.yml .dd)

if [ -z "$SLUG" ] && [ -f demo.yaml ]; then
  SLUG="$(sed -nE 's/^slug:[[:space:]]*([a-z0-9-]+).*/\1/p' demo.yaml | head -1)"
fi
SLUG="${SLUG:-demo-depot-starter}"

run() { if [ "$DRY" = 1 ]; then echo "  (dry-run) $*"; else "$@"; fi; }
say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

echo "Repo:  $ROOT"
echo "Slug:  $SLUG"
[ "$DRY" = 1 ] && echo "Mode:  dry-run, nothing will change"

if [ "$YES" != 1 ] && [ "$DRY" != 1 ]; then
  printf '\nThis deletes the demo from Demo Depot, the v* tags, and the depot files listed above. Continue? [y/N] '
  read -r ans
  case "$ans" in y|Y|yes) ;; *) echo "aborted"; exit 1 ;; esac
fi

# 1. Demo Depot -----------------------------------------------------------------------------------
if [ "$DO_DEPOT" = 1 ]; then
  say "1. Demo Depot"
  CFG="${XDG_CONFIG_HOME:-$HOME/.config}/demo-depot/config.json"
  if [ -z "${DD_TOKEN:-}" ] && [ -f "$CFG" ]; then
    DD_TOKEN="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("token",""))' "$CFG")"
    DD_URL="${DD_URL:-$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("url",""))' "$CFG")}"
  fi
  DD_URL="${DD_URL:-https://demodepot.launchdarklydemos.com}"
  if [ -z "${DD_TOKEN:-}" ]; then
    echo "  no Demo Depot token: run 'ddu auth login' or set DD_TOKEN. Skipping the depot step." >&2
  else
    code="$(curl -sS -o /tmp/dd-reset-get.json -w '%{http_code}' -H "Authorization: Bearer $DD_TOKEN" "$DD_URL/api/demos/$SLUG")"
    case "$code" in
      200)
        python3 - /tmp/dd-reset-get.json <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(f"  found '{d['demo'].get('name', '')}' with {len(d.get('versions', []))} version(s): " + ", ".join(f"{v['version']} ({v['status']})" for v in d.get("versions", [])))
PY
        if [ "$DRY" = 1 ]; then
          echo "  (dry-run) DELETE $DD_URL/api/demos/$SLUG?teardown=1"
        else
          dcode="$(curl -sS -o /tmp/dd-reset-del.json -w '%{http_code}' -X DELETE -H "Authorization: Bearer $DD_TOKEN" "$DD_URL/api/demos/$SLUG?teardown=1")"
          if [ "$dcode" = 200 ]; then
            python3 - /tmp/dd-reset-del.json <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
print(f"  deleted: {r.get('instancesTornDown', 0)} instance(s) torn down, {r.get('itemsDeleted', 0)} record(s), {r.get('objectsDeleted', 0)} object(s), images: {', '.join(r.get('repositoriesDeleted', [])) or 'none'}")
PY
          else
            echo "  delete failed (HTTP $dcode): $(cat /tmp/dd-reset-del.json)" >&2
            exit 1
          fi
        fi
        ;;
      404) echo "  '$SLUG' is not in the depot. Nothing to delete." ;;
      *) echo "  depot API returned HTTP $code: $(cat /tmp/dd-reset-get.json)" >&2; exit 1 ;;
    esac
    rm -f /tmp/dd-reset-get.json /tmp/dd-reset-del.json
  fi
fi

# 2. Tags -----------------------------------------------------------------------------------------
if [ "$DO_TAGS" = 1 ]; then
  say "2. Git tags"
  git fetch --tags -q origin 2>/dev/null || true
  tags="$(git tag -l 'v*')"
  if [ -z "$tags" ]; then
    echo "  no v* tags"
  else
    for t in $tags; do
      echo "  deleting $t"
      run git tag -d "$t" >/dev/null
      if git ls-remote --exit-code --tags origin "refs/tags/$t" >/dev/null 2>&1; then
        run git push -q origin ":refs/tags/$t"
      fi
    done
  fi
fi

# 3. Files ----------------------------------------------------------------------------------------
if [ "$DO_FILES" = 1 ]; then
  say "3. Depot artifacts"
  for f in "${ARTIFACTS[@]}"; do
    if [ -e "$f" ]; then
      echo "  removing $f"
      run rm -rf "$f"
    fi
  done
fi

say "Done."
cat <<MSG
The app in web/ is untouched. Next, in Claude Code:
  "Using the demo-depot skill, make this repo ready for Demo Depot."
then ddu validate . and git tag v0.1.0 && git push origin v0.1.0 to publish.
Commit the removal if you want the clean state on the branch: git add -A && git commit -m "Reset for the depot walkthrough"
MSG
