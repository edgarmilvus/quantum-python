#!/usr/bin/env bash
# Run every chapter's harness and exercises, without a key or a network.
set -euo pipefail

cd "$(dirname "$0")"
PY="${PYTHON:-.venv/bin/python}"
case "$PY" in /*) ;; *) PY="$(pwd)/${PY}" ;; esac
CHAPTER="${1:-all}"

run_chapter() {
  local id="$1"
  local dir="chapters/${id}/files"
  local number=$((10#${id#chapter}))
  echo "== ${id}"
  if [ -f "${dir}/run_ex${number}.py" ]; then
    (cd "$dir" && PYTHONPATH=. "${PY}" "run_ex${number}.py")
  fi
  if [ -f "${dir}/exercises/run_exercises.py" ]; then
    (cd "${dir}/exercises" && PYTHONPATH="..:." "${PY}" run_exercises.py)
  fi
}

if [ "$CHAPTER" = "all" ]; then
  for files in chapters/chapter*/files; do
    run_chapter "$(basename "$(dirname "$files")")"
  done
else
  run_chapter "$CHAPTER"
fi
