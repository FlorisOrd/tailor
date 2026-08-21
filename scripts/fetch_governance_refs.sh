#!/usr/bin/env bash
set -euo pipefail

case "${1-}" in
  Username*) printf '%s\n' 'x-access-token'; exit 0 ;;
  Password*) printf '%s\n' "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"; exit 0 ;;
esac

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"
export GIT_ASKPASS="$PWD/scripts/fetch_governance_refs.sh"
export GIT_TERMINAL_PROMPT=0

git fetch --no-tags origin \
  '+refs/governance/authorizations/*:refs/governance/authorizations/*' \
  '+refs/governance/bootstrap-gates/*:refs/governance/bootstrap-gates/*'

authorization_ref="$(git for-each-ref --format='%(refname)' refs/governance/authorizations/ | head -n 1)"
gate_ref="$(git for-each-ref --format='%(refname)' refs/governance/bootstrap-gates/ | head -n 1)"
test -n "$authorization_ref"
test -n "$gate_ref"
git cat-file -e "${authorization_ref}^{commit}"
git cat-file -e "${gate_ref}^{commit}"
printf '%s\n' 'authenticated_governance_refs=verified'
