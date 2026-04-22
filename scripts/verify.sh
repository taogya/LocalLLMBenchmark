#!/usr/bin/env bash
# TASK-00004-03: トレーサビリティ機械チェックの集約実行スクリプト。
#
# - scripts/traceability/check_*.py を順次実行
# - 1 つが失敗しても継続し、最後に集約結果を表示
# - 1 件でも失敗があれば exit 1
#
# 使い方: bash scripts/verify.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TRACE_DIR="${SCRIPT_DIR}/traceability"

PYTHON="${PYTHON:-python3}"

CHECKS=(
  "check_id_format.py"
  "check_id_uniqueness.py"
  "check_id_references.py"
  "check_doc_links.py"
  "check_progress_format.py"
  "check_mermaid_syntax.py"
  "check_markdown_syntax.py"
  "check_no_implementation_leak.py"
  "check_role_boundary.py"
  "check_oos_no_implementation.py"
)

declare -a RESULTS
overall=0

cd "${ROOT_DIR}"

for script in "${CHECKS[@]}"; do
  echo "================================================================"
  echo "[RUN] ${script}"
  echo "----------------------------------------------------------------"
  "${PYTHON}" "${TRACE_DIR}/${script}"
  rc=$?
  RESULTS+=("${rc} ${script}")
  if [[ ${rc} -ne 0 ]]; then
    overall=1
  fi
done

echo "================================================================"
echo "Summary"
echo "----------------------------------------------------------------"
for entry in "${RESULTS[@]}"; do
  rc="${entry%% *}"
  script="${entry#* }"
  if [[ "${rc}" == "0" ]]; then
    echo "  OK    ${script}"
  else
    echo "  FAIL  ${script} (exit=${rc})"
  fi
done
echo "================================================================"

exit "${overall}"
