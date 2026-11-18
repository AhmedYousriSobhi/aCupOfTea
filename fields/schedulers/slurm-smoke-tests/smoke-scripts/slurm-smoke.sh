#!/usr/bin/env bash
# slurm-smoke.sh - a two-minute control-plane check.
# Exit status: 0 = every check passed
#              1 = at least one check failed
#              2 = nothing failed, but a test job had to wait for a busy cluster (inconclusive)
# Run it as an ordinary user who may submit jobs, not as root.
#
#   SMOKE_PARTITION=gpu ./slurm-smoke.sh
#
set -u
PART_OPT=()
[ -n "${SMOKE_PARTITION:-}" ] && PART_OPT=(-p "$SMOKE_PARTITION")
LIMIT=${SMOKE_TIMEOUT:-60}          # seconds each step may take
TIME=${SMOKE_TIME:-2}               # --time (minutes) for the test jobs; many sites refuse jobs without one
WORK=$(mktemp -d)
JOBS=()
cleanup() { [ ${#JOBS[@]} -gt 0 ] && scancel "${JOBS[@]}" 2>/dev/null; rm -rf "$WORK"; }
trap cleanup EXIT
status=0                            # 0 pass, 2 inconclusive, 1 fail (1 wins)

pass() { printf 'PASS  %-8s %s\n' "$1" "$2"; }
wait_() { printf 'WAIT  %-8s %s\n' "$1" "$2"; [ $status -eq 0 ] && status=2; }
bad()  { printf 'FAIL  %-8s %s\n' "$1" "$2"; status=1; }

# 1. MUNGE: can this host make and read a credential?
if munge -n 2>/dev/null | unmunge 2>/dev/null | grep -q 'STATUS: *Success'; then
    pass munge "credential encoded and decoded"
else
    bad munge "munge -n | unmunge did not return Success"
fi

# 2. Is the controller (and the backup, if any) answering?
out=$(timeout "$LIMIT" scontrol ping 2>&1)
if [ $? -eq 0 ] && ! echo "$out" | grep -q DOWN; then pass ping "$(echo "$out" | head -1)"
else bad ping "$(echo "$out" | grep -m1 -E 'DOWN|error|fail' || echo "$out" | head -1)"; fi

# 3. Any node down, drained, failing, or silent (a trailing * means not responding)?
total=0
if out=$(timeout "$LIMIT" sinfo -h -N "${PART_OPT[@]}" -o '%N %T' 2>&1); then
    total=$(echo "$out" | grep -c .)
    badnodes=$(echo "$out" | grep -E 'down|drain|fail|\*' || true)
    if [ -z "$badnodes" ]; then pass nodes "$total node(s), none down or drained"
    else bad nodes "$(echo "$badnodes" | tr '\n' ';')"; fi
else
    bad nodes "sinfo: $(echo "$out" | head -1)"
fi

# 4. Can one task start on every node at once?  --immediate: do not queue behind real work.
if [ "$total" -gt 0 ]; then
    out=$(timeout "$LIMIT" srun --immediate="$(( LIMIT > 1 ? LIMIT / 2 : 1 ))" -N "$total" -n "$total" -t "$TIME" "${PART_OPT[@]}" \
          bash -c 'echo "$SLURMD_NODENAME"' 2>&1); rc=$?
    got=$(echo "$out" | grep -v '^srun:' | sort -u | grep -c .)
    if [ $rc -eq 0 ] && [ "$got" -eq "$total" ]; then pass srun "$got of $total nodes answered"
    elif echo "$out" | grep -q 'nodes are busy\|Unable to allocate'; then wait_ srun "cluster is busy: $(echo "$out" | grep -m1 'error:' | sed 's/^srun: error: //')"
    elif [ $rc -eq 124 ]; then bad srun "no answer within ${LIMIT}s"
    else bad srun "rc=$rc: $(echo "$out" | grep -m1 -E 'error|fail' || echo "$out" | head -1)"; fi
fi

# 5. Batch path: submit, poll until it leaves the queue, read the output file.
jid=$(timeout "$LIMIT" sbatch --parsable -t "$TIME" "${PART_OPT[@]}" -o "$WORK/out.txt" --wrap='echo smoke-ok' 2>&1)
if ! [[ "$jid" =~ ^[0-9]+ ]]; then
    bad sbatch "submit refused: $(echo "$jid" | head -1)"; jid=""
else
    jid=${jid%%;*}; JOBS+=("$jid")
    for ((t=0; t<LIMIT; t++)); do
        sq=$(squeue -h -j "$jid" -o '%T|%r' 2>/dev/null)
        [ -z "$sq" ] && break
        sleep 1
    done
    if [ -z "$sq" ] && grep -q smoke-ok "$WORK/out.txt" 2>/dev/null; then pass sbatch "job $jid ran and wrote its output"
    elif [ -n "$sq" ] && [[ "$sq" == PENDING* ]]; then wait_ sbatch "job $jid still pending after ${LIMIT}s (${sq#*|})"
    elif [ -n "$sq" ]; then bad sbatch "job $jid still ${sq%%|*} after ${LIMIT}s"
    else bad sbatch "job $jid left the queue but wrote no output"; fi
fi

# 6. Accounting: did the database record that job as COMPLETED?
if [ -n "$jid" ] && [ -z "${sq:-}" ]; then
    state=""
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        state=$(timeout 10 sacct -n -X -P -j "$jid" -o State 2>/dev/null | head -1)
        [ "$state" = COMPLETED ] && break
        sleep 1
    done
    if [ "$state" = COMPLETED ]; then pass sacct "job $jid recorded as COMPLETED"
    else bad sacct "job $jid in the database: '${state:-nothing}'"; fi
fi

case $status in 0) echo "ALL PASS";; 2) echo "INCONCLUSIVE (cluster busy, nothing failed)";; *) echo "FAILED";; esac
exit $status
