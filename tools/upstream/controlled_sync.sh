#!/usr/bin/env bash
set -euo pipefail
trap 'echo "controlled upstream sync failed at line $LINENO: $BASH_COMMAND" >&2' ERR

UPSTREAM_URL="${UPSTREAM_URL:-https://github.com/andrewhack/stremio-libtorrent-server.git}"
UPSTREAM_NAME="${UPSTREAM_NAME:-andrewhack/stremio-libtorrent-server}"
TARGET_BRANCH="${TARGET_BRANCH:-upstream/integration}"

git config user.name "${GIT_AUTHOR_NAME:-github-actions[bot]}"
git config user.email "${GIT_AUTHOR_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"

git remote add upstream "$UPSTREAM_URL" 2>/dev/null || git remote set-url upstream "$UPSTREAM_URL"
git fetch --prune origin main
git fetch --prune upstream main

MAIN_SHA="$(git rev-parse origin/main)"
TARGET_SHA="$(git rev-parse upstream/main)"
TARGET_VERSION="$(git show "$TARGET_SHA:pyproject.toml" | sed -n 's/^version = "\(.*\)"/\1/p' | head -1)"
SHORT="${TARGET_SHA:0:12}"
REPORT="/tmp/upstream-controlled-sync.md"

is_protected() {
    local candidate="$1" protected
    while IFS= read -r protected; do
        [ -n "$protected" ] || continue
        case "$protected" in \#*) continue ;; esac
        if [ "$candidate" = "$protected" ] || [ "${candidate#"$protected"/}" != "$candidate" ]; then
            return 0
        fi
    done < .github/upstream-protected-paths.txt
    return 1
}

restore_from_main() {
    local path="$1" entry mode blob

    if git cat-file -e "$MAIN_SHA:$path" 2>/dev/null; then
        entry="$(git ls-tree "$MAIN_SHA" -- "$path")"
        mode="$(printf '%s\n' "$entry" | awk '{print $1}')"
        blob="$(printf '%s\n' "$entry" | awk '{print $3}')"

        test -n "$mode"
        test -n "$blob"

        # Preserve the exact Git blob from fork main. Using checkout/add here can
        # normalize CRLF/LF through attributes and create a false protected-path
        # modification even when the logical content is identical.
        git update-index --add --cacheinfo "$mode,$blob,$path"

        mkdir -p "$(dirname "$path")"
        if [ "$mode" = "120000" ]; then
            rm -f -- "$path"
            ln -s "$(git cat-file blob "$blob")" "$path"
        else
            git cat-file blob "$blob" > "$path"
            [ "$mode" = "100755" ] && chmod +x "$path" || true
        fi
    else
        git rm -rf --ignore-unmatch -- "$path" >/dev/null 2>&1 || true
    fi
}

if git merge-base --is-ancestor "$TARGET_SHA" "$MAIN_SHA"; then
    {
        echo "# Controlled upstream sync"
        echo
        echo "Fork main already contains principal main."
        echo
        echo "- Principal: `$UPSTREAM_NAME`"
        echo "- Version: `$TARGET_VERSION`"
        echo "- SHA: `$TARGET_SHA`"
        echo "- Fork main: `$MAIN_SHA`"
    } > "$REPORT"
    cat "$REPORT"
    echo "UPSTREAM_SYNC_CHANGED=false" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
    exit 0
fi

git checkout -B "$TARGET_BRANCH" "$MAIN_SHA"

set +e
git merge --no-ff --no-commit upstream/main
merge_rc=$?
set -e

if [ "$merge_rc" -ne 0 ]; then
    mapfile -t conflicts < <(git diff --name-only --diff-filter=U)

    for path in "${conflicts[@]}"; do
        if is_protected "$path"; then
            echo "Resolving protected conflict in favor of fork: $path"
            restore_from_main "$path"
        fi
    done

    mapfile -t remaining < <(git diff --name-only --diff-filter=U)
    if [ "${#remaining[@]}" -gt 0 ]; then
        {
            echo "# Controlled upstream sync blocked"
            echo
            echo "- Principal: `$UPSTREAM_NAME`"
            echo "- Principal version: `$TARGET_VERSION`"
            echo "- Principal SHA: `$TARGET_SHA`"
            echo "- Fork main: `$MAIN_SHA`"
            echo
            echo "## Manual conflicts"
            echo
            for path in "${remaining[@]}"; do
                echo "- `$path`"
            done
            echo
            echo "Protected conflicts were automatically resolved in favor of the fork."
            echo "No branch was pushed and main was not changed."
        } > "$REPORT"

        cp "$REPORT" upstream-sync-report.md
        git merge --abort || true
        cat "$REPORT"
        echo "UPSTREAM_SYNC_BLOCKED=true" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
        exit 2
    fi
fi

# Restore every protected path changed by the merge, not just explicit conflicts.
mapfile -t changed_paths < <(git diff --name-only "$MAIN_SHA")
for path in "${changed_paths[@]}"; do
    if is_protected "$path"; then
        echo "Restoring fork-owned path: $path"
        restore_from_main "$path"
    fi
done

# The baseline marker is the one protected file that intentionally advances
# after a successful controlled merge.
printf '%s\n' "$TARGET_SHA" > .github/UPSTREAM_BASE
git add .github/UPSTREAM_BASE

if git diff --cached --quiet && git diff --quiet; then
    echo "No effective file changes after fork protections; recording upstream history only."
fi

git commit -m "Merge upstream $TARGET_VERSION ($SHORT) with fork protections"

{
    echo "# Controlled upstream sync"
    echo
    echo "- Principal: `$UPSTREAM_NAME`"
    echo "- Principal version: `$TARGET_VERSION`"
    echo "- Principal SHA: `$TARGET_SHA`"
    echo "- Fork base: `$MAIN_SHA`"
    echo "- Integration branch: `$TARGET_BRANCH`"
    echo
    echo "## Imported principal commits"
    echo
    git log --reverse --pretty='- `%h` %s' "$MAIN_SHA..$TARGET_SHA" 2>/dev/null || true
    echo
    echo "## Protected fork paths restored"
    echo
    protected_any=0
    for path in "${changed_paths[@]}"; do
        if is_protected "$path"; then
            echo "- `$path`"
            protected_any=1
        fi
    done
    if [ "$protected_any" -eq 0 ]; then
        echo "- None"
    fi
    echo
    echo "The branch contains a real merge of principal history. CI must pass before it can be merged to main."
} > "$REPORT"

cp "$REPORT" upstream-sync-report.md

git push --force-with-lease origin "$TARGET_BRANCH"

if [ -n "${GH_TOKEN:-}" ] && command -v gh >/dev/null 2>&1; then
    title="Sync principal $TARGET_VERSION ($SHORT)"
    body="$(mktemp)"
    cat "$REPORT" > "$body"
    cat >> "$body" <<'EOF'

## Validation gate

This pull request must pass the fork CI before merge. The merge is never performed directly into main by automation.
EOF

    existing="$(gh pr list --base main --head "$TARGET_BRANCH" --state open --json number --jq '.[0].number // empty')"
    if [ -n "$existing" ]; then
        gh pr edit "$existing" --title "$title" --body-file "$body"
    else
        gh pr create --base main --head "$TARGET_BRANCH" --title "$title" --body-file "$body"
    fi
fi

cat "$REPORT"
echo "UPSTREAM_SYNC_CHANGED=true" >> "${GITHUB_ENV:-/dev/null}" 2>/dev/null || true
