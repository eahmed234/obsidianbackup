#!/usr/bin/env bash
# Rewrite and verify a list of notes with Claude Code, one fresh session per step.
#
#   ./rewrite-queue.sh                 # reads review/queue.txt — one note name per line, # for comments
#   MODEL=opus ./rewrite-queue.sh big.txt
#   QUIET=1 ./rewrite-queue.sh         # one line per step instead of live progress
#
# Finished notes are recorded in review/done.txt and skipped next time, so the script can be stopped
# (Ctrl-C) and restarted, or re-run after a usage limit resets. It stops at the first failure.
# Nothing is pushed: publish afterwards with  git push origin drafts:main
set -u -o pipefail
cd "$(dirname "$0")"
QUEUE="${1:-review/queue.txt}"
MODEL="${MODEL:-sonnet}"
QUIET="${QUIET:-}"
LOGS=review/logs
mkdir -p "$LOGS"; touch review/done.txt

[ "$(git branch --show-current)" = "drafts" ] || { echo "Not on the drafts branch — stopping."; exit 1; }
[ -f "$QUEUE" ] || { echo "No queue file at $QUEUE"; exit 1; }

trim() {   # strip CR, surrounding spaces and a trailing .md
  local s="${1%$'\r'}"
  s="${s#"${s%%[![:space:]]*}"}"; s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "${s%.md}"
}

# Live progress: turn Claude Code's event stream into one short line per action.
progress() {
  python3 -u -c '
import json, sys, time
t0 = time.time()
def clock(): return time.strftime("%M:%S", time.gmtime(time.time() - t0))
def short(s, n=110):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + "…"
final = ""
for line in sys.stdin:
    try:
        ev = json.loads(line)
    except ValueError:
        if line.strip(): print("      " + short(line), flush=True)
        continue
    kind = ev.get("type")
    if kind == "assistant":
        for block in ev.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                i, name = block.get("input", {}), block.get("name", "?")
                what = i.get("command") or i.get("file_path") or i.get("pattern") or i.get("skill") or ""
                print(f"      {clock()}  {name:<5} {short(what)}", flush=True)
            elif block.get("type") == "text" and block.get("text", "").strip():
                final = block["text"].strip()
    elif kind == "result":
        final = (ev.get("result") or final).strip()
        cost = ev.get("total_cost_usd")
        turns = ev.get("num_turns", "?")
        money = ", ${:.2f} at API rates".format(cost) if isinstance(cost, (int, float)) else ""
        print("      {}  finished: {} turns{}{}".format(clock(), turns, money, " — ERROR" if ev.get("is_error") else ""), flush=True)
        if ev.get("is_error"):
            print("      " + short(final, 400), flush=True)
print("\n" + final + "\n")
' 
}

step() {   # step <skill> <note>
  local log="$LOGS/$2.$1.log" prompt="Follow .claude/skills/$1/SKILL.md for the note: $2"
  if [ -n "$QUIET" ]; then
    claude -p "$prompt" --model "$MODEL" --permission-mode acceptEdits < /dev/null > "$log" 2>&1
  else
    claude -p "$prompt" --model "$MODEL" --permission-mode acceptEdits \
        --output-format stream-json --verbose < /dev/null 2> "$log.err" \
      | tee "$log.jsonl" | progress | tee "$log" | grep -E '^      ' 
    return "${PIPESTATUS[0]}"
  fi
}

total=0; todo=0
while IFS= read -r line || [ -n "$line" ]; do
  n="$(trim "$line")"; case "$n" in ""|\#*) continue ;; esac
  total=$((total + 1)); grep -qxF -- "$n" review/done.txt || todo=$((todo + 1))
done < "$QUEUE"
echo "Queue: $QUEUE — $total notes, $((total - todo)) already done, $todo to do. Model: $MODEL."
echo "Each note: rewrite (builds the ledger if missing) → verify (fresh session) → audit."
[ -n "$QUIET" ] || echo "Lines below are the session's actions as they happen; full reports go to $LOGS/."

i=0; started=$(date +%s)
while IFS= read -r line || [ -n "$line" ]; do
  note="$(trim "$line")"
  case "$note" in ""|\#*) continue ;; esac
  grep -qxF -- "$note" review/done.txt && continue
  i=$((i + 1))
  [ -f "$note.md" ] || { echo "No such note: '$note' — stopping. (Names are the file names without .md.)"; exit 1; }
  echo
  echo "══ [$i/$todo] $note   $(date '+%H:%M')"
  before=$(git rev-parse --short HEAD)

  echo "  ── 1/3 rewrite"
  step rewrite-note "$note" || { echo "  ✗ rewrite failed — see $LOGS/$note.rewrite-note.log"; exit 1; }
  echo "  ── 2/3 verify"
  step verify-note  "$note" || { echo "  ✗ verify failed — see $LOGS/$note.verify-note.log"; exit 1; }
  echo "  ── 3/3 audit"
  python3 audit.py --no-content > /dev/null && python3 audit.py --ledger > /dev/null \
    || { echo "  ✗ audit fails after $note — stopping. Run: python3 audit.py --no-content"; exit 1; }
  flags=$(python3 audit.py --note "$note" | awk '/CONTENT TRIAGE/{f=1;next} f && $2 ~ /^[0-9]+$/ {s+=$2} END{print s+0}')
  echo "$note" >> review/done.txt

  echo "  ✓ done. Commits: $(git log --oneline "$before..HEAD" | wc -l | tr -d ' ')   audit flags on the note: $flags"
  report="review/$note.verify.md"
  if [ -f "$report" ]; then
    grep -m1 -E '^Supported' "$report" | sed 's/^/    /'
    awk '/^## For you/{f=1;next} f && NF' "$report" | sed 's/^/    for you: /'
  else
    echo "    (no verify report was written — check $LOGS/$note.verify-note.log)"
  fi
done < "$QUEUE"

mins=$(( ($(date +%s) - started) / 60 ))
echo
echo "Queue finished: $i notes in $mins min. Reports: review/<note>.verify.md. Nothing pushed."
