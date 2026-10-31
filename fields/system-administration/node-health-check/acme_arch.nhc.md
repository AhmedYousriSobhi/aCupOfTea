# acme_arch.nhc

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/system-administration/node-health-check/acme_arch.nhc)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/system-administration/node-health-check/acme_arch.nhc)

</div>

```bash
# NHC -- ACME architecture checks (used by configs generated with nhc_gen.py)
#
# aCupOfTea NHC series, part 9. License: BSD-3, same as NHC.
#
# Checks:
#   check_arch_numa_nodes <count>          NUMA nodes online == count
#   check_arch_gpu_count <count>           GPUs visible to nvidia-smi == count
#   check_arch_gpu_model <substring>       every GPU's name contains substring
#   check_arch_dcgm_diag <level> [secs]    dcgmi diag -r <level> has no failing test

declare -g  ARCH_NVSMI="${ARCH_NVSMI:-/usr/bin/nvidia-smi}"
declare -g  ARCH_NUMA_ONLINE="${ARCH_NUMA_ONLINE:-/sys/devices/system/node/online}"
declare -ga ARCH_GPU_NAMES=( )
declare -g  ARCH_GPU_GATHERED=0
declare -g  ARCH_GPU_RC=0

function nhc_arch_gpu_gather_data() {
    local IFS=$'\n'
    ARCH_GPU_NAMES=( $(timeout 20 "$ARCH_NVSMI" --query-gpu=name --format=csv,noheader 2>/dev/null) )
    ARCH_GPU_RC=$?
    ARCH_GPU_GATHERED=1
}

function check_arch_numa_nodes() {
    local EXPECTED="$1" LIST RANGE COUNT=0 LO HI
    if ! read -r LIST < "$ARCH_NUMA_ONLINE"; then
        die 1 "${FUNCNAME[0]}:  cannot read $ARCH_NUMA_ONLINE"
        return 1
    fi
    # Format is a cpulist such as "0-7" or "0,2-3"
    local IFS=','
    for RANGE in $LIST; do
        if [[ "$RANGE" == *-* ]]; then
            LO="${RANGE%-*}" HI="${RANGE#*-}"
            (( COUNT += HI - LO + 1 ))
        else
            COUNT=$(( COUNT + 1 ))
        fi
    done
    if (( COUNT != EXPECTED )); then
        die 1 "${FUNCNAME[0]}:  $COUNT NUMA nodes online ($LIST), expected $EXPECTED"
        return 1
    fi
    return 0
}

function check_arch_gpu_count() {
    local EXPECTED="$1"
    (( ARCH_GPU_GATHERED )) || nhc_arch_gpu_gather_data
    if (( ARCH_GPU_RC != 0 )); then
        die 1 "${FUNCNAME[0]}:  nvidia-smi failed or timed out (rc=$ARCH_GPU_RC)"
        return 1
    fi
    if (( ${#ARCH_GPU_NAMES[@]} != EXPECTED )); then
        die 1 "${FUNCNAME[0]}:  ${#ARCH_GPU_NAMES[@]} GPUs visible, expected $EXPECTED"
        return 1
    fi
    return 0
}

function check_arch_gpu_model() {
    local WANT="$1" NAME IDX=0
    (( ARCH_GPU_GATHERED )) || nhc_arch_gpu_gather_data
    for NAME in "${ARCH_GPU_NAMES[@]}"; do
        if [[ "$NAME" != *"$WANT"* ]]; then
            die 1 "${FUNCNAME[0]}:  GPU $IDX is '$NAME', expected '$WANT'"
            return 1
        fi
        IDX=$(( IDX + 1 ))
    done
    return 0
}

# Slow (level 2 is minutes and loads the GPUs): only for the nhc-deep context.
# Verify the failure text on your DCGM version; see part 6 of the series.
function check_arch_dcgm_diag() {
    local LEVEL="${1:-1}" TMO="${2:-600}"
    check_cmd_output -C "${FUNCNAME[0]}" -t "$TMO" -r 0 \
        -m '!/Fail/' -M "dcgmi diag -r $LEVEL reported a failing test" \
        -e "dcgmi diag -r $LEVEL"
}
```
