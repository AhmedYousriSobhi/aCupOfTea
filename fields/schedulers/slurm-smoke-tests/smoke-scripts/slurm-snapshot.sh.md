# slurm-snapshot.sh

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-snapshot.sh)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/fields/schedulers/slurm-smoke-tests/smoke-scripts/slurm-snapshot.sh)

</div>

```bash
#!/usr/bin/env bash
# slurm-snapshot.sh DIR - save what a Slurm change could alter, as plain text, so diff can compare.
#   ./slurm-snapshot.sh /tmp/before ; (make the change) ; ./slurm-snapshot.sh /tmp/after ; diff -ru /tmp/before /tmp/after
set -u
d=${1:?usage: slurm-snapshot.sh DIR}; mkdir -p "$d"
# configuration the controller is actually running (minus the lines that change every second)
scontrol show config | grep -v -E '^Configuration data as of|^BOOT_TIME|^SLURM_CONF'  > "$d/config.txt"
scontrol show partition   > "$d/partitions.txt"
scontrol show node -o | sed -E 's/ (CPULoad|FreeMem|AllocMem|LastBusyTime|BootTime|SlurmdStartTime|ResumeAfterTime|CfgTRES|AllocTRES|AllocCPUs)=[^ ]*//g' | sort > "$d/nodes.txt"
scontrol show reservation > "$d/reservations.txt" 2>&1
sacctmgr -nP show qos  format=Name,Priority,Preempt,PreemptMode,GraceTime,Flags > "$d/qos.txt" 2>&1
sacctmgr -nP show assoc format=Account,User,Partition,QOS,DefaultQOS,GrpTRES,MaxJobs | sort > "$d/associations.txt" 2>&1
squeue -h -t R,PD -o '%T' | sort | uniq -c > "$d/queue-counts.txt"
echo "snapshot saved in $d: $(ls "$d" | tr '\n' ' ')"
```
