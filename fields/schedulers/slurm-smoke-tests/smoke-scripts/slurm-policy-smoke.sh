#!/usr/bin/env bash
# slurm-policy-smoke.sh - does the cluster still enforce the QOS/preemption policy?
# Run as an ordinary user who belongs to ACCT and may use QOS low and high_<ACCT>.
#   ACCT=physics PART=gpu ./slurm-policy-smoke.sh
# Stage 1 uses no resources (held jobs and --test-only). Stage 2 evicts a real job on one node.
set -u
ACCT=${ACCT:?set ACCT, account of the test user}
PART=${PART:?set PART, the partition to test}
WAIT=${WAIT:-150}                       # seconds to wait for each state change
NODE=${NODE:-$(sinfo -h -p "$PART" -t idle -o %n | head -1)}
WORK=$(mktemp -d); JOBS=(); pass=0; fail=0
cleanup() { [ ${#JOBS[@]} -gt 0 ] && scancel "${JOBS[@]}" 2>/dev/null; rm -rf "$WORK"; }
trap cleanup EXIT
ok()  { echo "  PASS  $*"; pass=$((pass+1)); }
bad() { echo "  FAIL  $*"; fail=$((fail+1)); }
state() { squeue -h -j "$1" -o %T 2>/dev/null; }
qos()   { squeue -h -j "$1" -o %q 2>/dev/null; }
until_state() { local t=0; while [ $t -lt "$WAIT" ]; do [ "$(state "$1")" = "$2" ] && return 0; sleep 2; t=$((t+2)); done; return 1; }

echo "== Stage 1: routing and rules (no resources used)"
id=$(sbatch --parsable --hold -t 5 -p "$PART" -A "$ACCT" --wrap=true 2>&1) && JOBS+=("$id")
[ "$(qos "$id")" = low ] && ok "no --qos becomes low" || bad "no --qos gave '$(qos "$id")'"
id=$(sbatch --parsable --hold -t 5 -p "$PART" -A "$ACCT" --qos=high --wrap=true 2>&1) && JOBS+=("$id")
[ "$(qos "$id")" = "high_$ACCT" ] && ok "--qos=high becomes high_$ACCT" || bad "--qos=high gave '$(qos "$id")'"
out=$(sbatch --test-only -p "$PART" -A "$ACCT" --wrap=true 2>&1)
echo "$out" | grep -q 'set --time' && ok "a job without --time is refused" || bad "no --time was not refused: $(echo "$out" | head -1)"

echo "== Stage 2: a high job evicts a low job on node ${NODE:-?}"
if [ -z "$NODE" ]; then bad "no idle node in $PART to test on"; else
cat > "$WORK/low.sh" <<'JOB'
#!/bin/bash
echo "START restart=${SLURM_RESTART_COUNT:-0} $(date +%T)"
sleep 600
JOB
chmod 755 "$WORK/low.sh"
low=$(sbatch --parsable -t 15 -p "$PART" -A "$ACCT" -w "$NODE" --exclusive --requeue -o "$WORK/low.out" --open-mode=append "$WORK/low.sh") && JOBS+=("$low")
until_state "$low" RUNNING && ok "low job $low running (qos $(qos "$low"))" || bad "low job never ran (state $(state "$low"))"
high=$(sbatch --parsable -t 2 -p "$PART" -A "$ACCT" -w "$NODE" --exclusive --qos=high --wrap='sleep 15') && JOBS+=("$high")
until_state "$high" RUNNING && ok "high job $high got the node (qos $(qos "$high"))" || bad "high job never ran (state $(state "$high"), reason $(squeue -h -j "$high" -o %r))"
sleep 3
r=$(scontrol show job "$low" 2>/dev/null | grep -o 'Restarts=[0-9]*' | cut -d= -f2)
[ "${r:-0}" -ge 1 ] && ok "low job was requeued (Restarts=$r)" || bad "low job shows Restarts=${r:-0}: cancelled instead of requeued?"
until_state "$low" RUNNING && ok "low job restarted once the high job finished" || bad "low job did not restart (state $(state "$low"))"
echo "  log:"; sed 's/^/    /' "$WORK/low.out"
fi
echo "== $pass passed, $fail failed"; [ $fail -eq 0 ]
