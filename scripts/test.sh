#!/usr/bin/env bash
# Runs the project's checks and tests. Designed for CI, works locally too.
#
# Usage:
#   scripts/test.sh            # everything
#   scripts/test.sh repo       # repository sanity checks only
#   scripts/test.sh backend    # Maven tests (JUnit, in-memory H2 - no MySQL needed)
#   scripts/test.sh frontend   # npm install + Jest tests + production build
#
# Env:
#   SKIP_FRONTEND_BUILD=1      # skip `npm run build` in the frontend step
#   SKIP_INSTALL=1             # skip `npm ci` (deps already installed / cached)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-all}"
FAILED=()

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[32m  ok\033[0m  %s\n' "$*"; }
fail() { printf '\033[31m  FAIL\033[0m %s\n' "$*"; }

require() {
  command -v "$1" >/dev/null 2>&1 || { fail "'$1' is not installed"; return 1; }
}

# ---------------------------------------------------------------- repo checks
test_repo() {
  log "Repository sanity checks"
  local rc=0 f

  for f in README.md .env.example backend/pom.xml frontend/package.json \
           frontend/package-lock.json frontend/src/config/ApplicationConfig.js \
           backend/src/main/resources/application.properties \
           backend/src/test/resources/application.properties; do
    if [[ -f "$ROOT/$f" ]]; then ok "$f exists"; else fail "$f is missing"; rc=1; fi
  done

  # Real .env files must never be committed (README section 4).
  if git -C "$ROOT" ls-files --error-unmatch '.env' 'backend/.env' 'frontend/.env' >/dev/null 2>&1; then
    fail ".env file is tracked by git"; rc=1
  else
    ok "no .env file tracked by git"
  fi

  # Every variable the app reads must be documented in .env.example.
  local var
  for var in DATASOURCE_URL DATASOURCE_USER DATASOURCE_PASSWORD REACT_APP_ROOT_SERVER; do
    if grep -q "^${var}=" "$ROOT/.env.example"; then ok ".env.example defines $var"
    else fail ".env.example is missing $var"; rc=1; fi
  done

  # Backend must take DB credentials from env, not hardcode them.
  if grep -Eq '^spring\.datasource\.(url|username|password)=\$\{' \
       "$ROOT/backend/src/main/resources/application.properties"; then
    ok "backend datasource is configured via env variables"
  else
    fail "backend datasource is not configured via env variables"; rc=1
  fi
  if grep -Eq '^spring\.datasource\.password=[^$]' \
       "$ROOT/backend/src/main/resources/application.properties"; then
    fail "hardcoded datasource password in application.properties"; rc=1
  fi

  # Frontend context path must match backend context path.
  if grep -q 'ROOT_URI = "/dev"' "$ROOT/frontend/src/config/ApplicationConfig.js" &&
     grep -q '^server.servlet.context-path=/dev' "$ROOT/backend/src/main/resources/application.properties"; then
    ok "frontend ROOT_URI matches backend context-path (/dev)"
  else
    fail "frontend ROOT_URI and backend context-path differ"; rc=1
  fi

  return $rc
}

# -------------------------------------------------------------------- backend
test_backend() {
  log "Backend: mvn test (H2 in-memory DB from src/test/resources)"
  require java || return 1
  require mvn || return 1
  java -version 2>&1 | head -1
  (cd "$ROOT/backend" && mvn -B -ntp clean verify)
  ok "backend tests passed, artifact: backend/target/dev.war"
}

# ------------------------------------------------------------------- frontend
test_frontend() {
  log "Frontend: install, test, build"
  require node || return 1
  require npm || return 1
  echo "node $(node -v), npm $(npm -v)"

  # react-scripts 4 / webpack 4 needs the legacy OpenSSL provider on Node >= 17.
  local major; major="$(node -p 'process.versions.node.split(".")[0]')"
  if (( major >= 17 )); then
    export NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--openssl-legacy-provider"
  fi

  cd "$ROOT/frontend"
  if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
    npm ci --legacy-peer-deps --no-audit --no-fund
  fi

  CI=true npx craco test --watchAll=false --passWithNoTests
  ok "frontend tests passed"

  if [[ "${SKIP_FRONTEND_BUILD:-0}" != "1" ]]; then
    # CI=false so existing lint warnings don't fail the build.
    CI=false npm run build
    ok "frontend build succeeded (frontend/build)"
  fi
}

run() {
  local name="$1" rc
  # Subshell keeps `cd`/exports isolated; set -e must not run in an `if` context
  # or bash silently disables it, so capture the exit code explicitly.
  set +e
  ( set -e; "test_$name" )
  rc=$?
  set -e
  (( rc == 0 )) || FAILED+=("$name")
}

case "$TARGET" in
  all)      run repo; run backend; run frontend ;;
  repo|backend|frontend) run "$TARGET" ;;
  *) echo "Unknown target '$TARGET' (use: all|repo|backend|frontend)"; exit 2 ;;
esac

echo
if (( ${#FAILED[@]} )); then
  fail "failed steps: ${FAILED[*]}"
  exit 1
fi
ok "all requested checks passed"
