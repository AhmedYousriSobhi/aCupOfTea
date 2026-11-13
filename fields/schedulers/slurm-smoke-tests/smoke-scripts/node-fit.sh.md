# node-fit.sh

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/node-fit.sh)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/node-fit.sh)

</div>

```bash
#!/usr/bin/env bash
# node-fit.sh NODENAME - run ON the node: does the hardware match what Slurm was told?
#   ./node-fit.sh node17
# Exit status: 0 = matches, 1 = a mismatch, 2 = could not read something.
set -u
node=${1:?usage: node-fit.sh NODENAME}
hw=$(slurmd -C 2>/dev/null | head -1) || exit 2
conf=$(scontrol show node "$node" -o 2>/dev/null) || { echo "controller does not know node $node"; exit 2; }
[ -n "$hw" ] && [ -n "$conf" ] || exit 2

get() { grep -o "$2=[0-9]*" <<<"$1" | head -1 | cut -d= -f2; }
hw_cpu=$(get "$hw" CPUs);        conf_cpu=$(get "$conf" CPUTot)
hw_mem=$(get "$hw" RealMemory);  conf_mem=$(get "$conf" RealMemory)
state=$(grep -o ' State=[A-Z+*~#]*' <<<"$conf" | head -1 | cut -d= -f2)
rc=0
if [ "$hw_cpu" = "$conf_cpu" ]; then echo "PASS  cpus    hardware $hw_cpu, configured $conf_cpu"
else echo "FAIL  cpus    hardware $hw_cpu, configured $conf_cpu"; rc=1; fi
if [ "$conf_mem" -le "$hw_mem" ]; then echo "PASS  memory  hardware ${hw_mem} MB, configured ${conf_mem} MB"
else echo "FAIL  memory  hardware ${hw_mem} MB, configured ${conf_mem} MB (configured is more than the node has)"; rc=1; fi
case "$state" in IDLE|MIXED|ALLOCATED) echo "PASS  state   $state";; *) echo "FAIL  state   $state"; rc=1;; esac
exit $rc
```
