#!/bin/bash
# silver-trade PR review runner — single-shot execution
set -u
REPO="jsmikelin/silver-trade"
API="https://api.github.com/repos/$REPO"
TMP=/tmp/silver_trade_review
mkdir -p "$TMP"

# 1. Token
TOKEN=$(echo "url=https://github.com" | git credential fill 2>/dev/null | grep '^password=' | cut -d= -f2)
if [ -z "$TOKEN" ]; then echo "FATAL: no token"; exit 2; fi

# 2. Open PRs
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "$API/pulls?state=open" -o "$TMP/open_prs.json"
if ! python -c "import json;d=json.load(open('$TMP/open_prs.json'));assert isinstance(d,list)" 2>/dev/null; then
  echo "API_ERROR:"; head -c 500 "$TMP/open_prs.json"; echo; exit 3
fi

PR_COUNT=$(python -c "import json;print(len(json.load(open('$TMP/open_prs.json'))))")
echo "OPEN_PR_COUNT=$PR_COUNT"
if [ "$PR_COUNT" -eq 0 ]; then
  echo "NO_OPEN_PRS"; exit 0
fi

# 3-4. Per PR: download diff, run verifier
python - "$TMP" <<'PYEOF'
import json, sys, subprocess, os
tmp = sys.argv[1]
prs = json.load(open(os.path.join(tmp, 'open_prs.json'), encoding='utf-8'))
for pr in prs:
    print(f"PR#{pr['number']}|{pr['title']}|author={pr['user']['login']}|head={pr['head']['ref']}|base={pr['base']['ref']}|updated={pr['updated_at']}")
PYEOF

for n in $(python -c "import json;[print(p['number']) for p in json.load(open('$TMP/open_prs.json'))]"); do
  echo "===== PR #$n ====="
  curl -s -L -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github.v3.diff" \
    "$API/pulls/$n" -o "$TMP/pr_$n.diff"
  echo "DIFF_BYTES=$(wc -c < "$TMP/pr_$n.diff")"
  python "C:/Users/Administrator/.hermes/website/silver-trade/verify_pr.py" --diff "$TMP/pr_$n.diff"
  echo "VERIFIER_EXIT=$?"
  # AI-code suspicion heuristics on added lines
  python - "$TMP/pr_$n.diff" <<'PYEOF'
import re, sys
diff = open(sys.argv[1], encoding='utf-8', errors='replace').read()
added = [l[1:] for l in diff.splitlines() if l.startswith('+') and not l.startswith('+++')]
flags = []
commented_code = 0
for l in added:
    s = l.strip()
    if re.match(r'^(#|//)\s*(print\(|def |class |import |from |if |for |while |return |const |let |var |function )', s):
        commented_code += 1
total_comments = sum(1 for l in added if l.strip().startswith('#'))
# comment ratio on added lines
if added:
    ratio = total_comments / len(added)
    if ratio > 0.4 and len(added) > 10:
        flags.append(f"high comment ratio {ratio:.0%} ({total_comments}/{len(added)} added lines)")
    if commented_code > 0:
        flags.append(f"{commented_code} commented-out code lines in additions")
    # unnatural identifiers (mixed transliteration / very long names)
    weird = [w for w in re.findall(r'\b[a-zA-Z_]\w{20,}\b', '\n'.join(added)) if w.lower() == w]
    if len(weird) > 3:
        flags.append(f"{len(weird)} very long snake_case identifiers (possible machine-generated): {', '.join(sorted(set(weird))[:5])}...")
print("AI_SUSPICION_FLAGS=" + ("; ".join(flags) if flags else "none"))
PYEOF
  echo "===== end PR #$n ====="
done
echo "ALL_DONE"
