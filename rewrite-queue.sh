#!/usr/bin/env bash
# Rewrite and verify a list of notes with Claude Code, one fresh session per step.
#
#   ./rewrite-queue.sh                 # reads review/queue.txt — one note name per line, # for comments
#   MODEL=opus ./rewrite-queue.sh big.txt
#
# Finished notes are recorded in review/done.txt and skipped next time, so the script can be stopped
# (Ctrl-C) and restarted, or re-run after a usage limit resets. It stops at the first failure.
# Nothing is pushed: publish afterwards with  git push origin drafts:main
set -u
cd "$(dirname "$0")"
QUEUE="${1:-review/queue.txt}"
MODEL="${MODEL:-sonnet}"
LOGS=review/logs
mkdir -p "$LOGS"; touch review/done.txt

[ "$(git branch --show-current)" = "drafts" ] || { echo "Not on the drafts branch — stopping."; exit 1; }
[ -f "$QUEUE" ] || { echo "No queue file at $QUEUE"; exit 1; }

step() {   # step <skill> <note>
  claude -p "Follow .claude/skills/$1/SKILL.md for the note: $2" \
    --model "$MODEL" --permission-mode acceptEdits < /dev/null > "$LOGS/$2.$1.log" 2>&1
}

while IFS= read -r note || [ -n "$note" ]; do
  note="${note%$'\r'}"                                   # tolerate Windows line ends
  note="${note#"${note%%[![:space:]]*}"}"                 # … and leading
  note="${note%"${note##*[![:space:]]}"}"                 # … and trailing spaces
  note="${note%.md}"
  case "$note" in ""|\#*) continue ;; esac
  grep -qxF -- "$note" review/done.txt && continue
  [ -f "$note.md" ] || { echo "No such note: $note — stopping."; exit 1; }
  echo "== $note   $(date '+%H:%M')"
  step rewrite-note "$note" || { echo "   rewrite failed — see $LOGS/$note.rewrite-note.log"; exit 1; }
  step verify-note  "$note" || { echo "   verify failed — see $LOGS/$note.verify-note.log"; exit 1; }
  python3 audit.py --no-content > /dev/null && python3 audit.py --ledger > /dev/null \
    || { echo "   audit fails after $note — stopping. Run: python3 audit.py --no-content"; exit 1; }
  echo "$note" >> review/done.txt
  echo "   done — review/$note.verify.md"
done < "$QUEUE"
echo "Queue finished."
