#!/bin/bash
# gpu_temp_scan.sh - dry run of the GPU temperature rules from parts 12 and 13.
#
# Read-only. Logs in to each node over ssh (several at a time), collects GPU
# temperature, utilization and memory in use with dcgmi, plus the Slurm node state
# with scontrol, and reports which GPUs the health check WOULD flag:
#   CEILING    any GPU above CEILING, in any node state          -> immediate drain
#   IDLE_HIGH  only on an IDLE node, for a GPU at 0% utilization with at most
#              IDLE_MEM_MAX MiB in use and above IDLE_MAX         -> warn, drain after WINDOW minutes
# MIXED and ALLOCATED nodes are checked against the ceiling only. A GPU with load or
# memory in use on an IDLE node (a test run, say) is BUSY(no job), not idle.
#
# Usage:  ./gpu_temp_scan.sh [nodelist.yml]
#
# nodelist.yml is a YAML list, one node per line (comments are ignored):
#   nodes:
#     - gpu-node-01
#     - gpu-node-02   # a trailing comment is fine
# Load your key once so ssh does not prompt for every node:
#   eval "$(ssh-agent -s)"; ssh-add
#
# Environment (defaults in brackets):
#   CEILING [87]  IDLE_MAX [45]  IDLE_MEM_MAX [1024]  WINDOW [10]  PARALLEL [20]
#   SSH_USER [none]  SSH_OPTS [see below]  OUT_DIR [gpu_temp_scan_<timestamp>]

set -u

load_settings() {
    nodes_file="${1:-nodelist.yml}"
    export CEILING="${CEILING:-87}"
    export IDLE_MAX="${IDLE_MAX:-45}"
    export IDLE_MEM_MAX="${IDLE_MEM_MAX:-1024}"
    export WINDOW="${WINDOW:-10}"
    parallel="${PARALLEL:-20}"
    export SSH_USER="${SSH_USER:-}"
    export OUT_DIR="${OUT_DIR:-gpu_temp_scan_$(date +%Y%m%d_%H%M%S)}"
    export SSH_OPTS="${SSH_OPTS:--o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=5 -o LogLevel=ERROR}"
}

preflight() {
    if [[ ! -f "$nodes_file" ]]; then
        echo "Node list not found: $nodes_file" >&2
        exit 1
    fi
    if ! ssh-add -l >/dev/null 2>&1; then
        echo "No ssh-agent keys loaded. Run:  eval \"\$(ssh-agent -s)\"; ssh-add   then run this again." >&2
        exit 1
    fi
    mkdir -p "$OUT_DIR/raw" || exit 1
}

node_names() {
    sed -nE 's/^[[:space:]]*-[[:space:]]+([^[:space:]#]+).*/\1/p' "$nodes_file"
}

# The read-only probe sent to every node. Each block starts with a ## marker.
probe_script() {
    cat <<'PROBE'
echo "##HOST";     hostname -s
echo "##DMON";     timeout 20 dcgmi dmon -e 150,203,252 -c 1 2>&1
echo "##SCONTROL"; timeout 15 scontrol show node "$(hostname -s)" 2>&1
PROBE
}

probe_node() {
    local node="$1"
    local dest="$node"
    local raw="$OUT_DIR/raw/$node"
    [[ -n "$SSH_USER" ]] && dest="$SSH_USER@$node"
    # SSH_OPTS is split on purpose: it holds several options.
    # shellcheck disable=SC2086
    if ! ssh $SSH_OPTS "$dest" "$(probe_script)" >"$raw.txt" 2>"$raw.err"; then
        echo "UNREACHABLE: $(head -1 "$raw.err")" >"$raw.fail"
    fi
}

collect_all() {
    export -f probe_node probe_script
    echo "Scanning $(node_names | wc -l) nodes (parallel $parallel)..." >&2
    node_names | xargs -P "$parallel" -I{} bash -c 'probe_node {}'
}

summarize() {
    python3 - "$OUT_DIR" "$nodes_file" <<'PY'
import collections
import csv
import os
import re
import sys

out_dir, nodes_file = sys.argv[1:3]
CEILING = int(os.environ["CEILING"])
IDLE_MAX = int(os.environ["IDLE_MAX"])
IDLE_MEM_MAX = int(os.environ["IDLE_MEM_MAX"])
WINDOW = os.environ["WINDOW"]
GPU_LINE = re.compile(r"\s*GPU\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)")
COLUMNS = ["node", "node_state", "gpu", "temp", "util", "mem_mib", "status", "trigger"]


NODE_ITEM = re.compile(r"^\s*-\s+([^\s#]+)")


def read_nodes(path):
    with open(path) as fh:
        return [m.group(1) for m in map(NODE_ITEM.match, fh) if m]


def split_blocks(text):
    blocks, name = collections.defaultdict(list), None
    for line in text.splitlines():
        if line.startswith("##"):
            name = line[2:].strip()
        elif name:
            blocks[name].append(line)
    return blocks


def as_int(token):
    return int(float(token)) if re.fullmatch(r"\d+(\.\d+)?", token) else None


def gpu_status(node_state, node_idle, util, mem):
    if node_state == "unknown":
        return "UNKNOWN"
    if not node_idle:
        return "ALLOCATED"
    if util is None or mem is None:
        return "UNKNOWN"
    if util == 0 and mem <= IDLE_MEM_MAX:
        return "IDLE"
    return "BUSY(no job)"


def triggers(temp, status):
    hit = []
    if temp > CEILING:
        hit.append("CEILING")
    if status == "IDLE" and temp > IDLE_MAX:
        hit.append("IDLE_HIGH")
    return "+".join(hit)


def scan(nodes):
    rows, unreachable, no_data, no_state = [], {}, {}, []
    for node in nodes:
        base = os.path.join(out_dir, "raw", node)
        if os.path.exists(base + ".fail"):
            with open(base + ".fail") as fh:
                unreachable[node] = fh.read().strip()
            continue
        try:
            with open(base + ".txt") as fh:
                blocks = split_blocks(fh.read())
        except OSError:
            unreachable[node] = "UNREACHABLE: no output"
            continue

        found = re.search(r"^\s*State=(\S+)", "\n".join(blocks["SCONTROL"]), re.M)
        node_state = found.group(1) if found else "unknown"
        if not found:
            no_state.append(node)
        node_idle = node_state.startswith("IDLE") and "COMPLETING" not in node_state

        seen = 0
        for line in blocks["DMON"]:
            m = GPU_LINE.match(line)
            temp = as_int(m.group(2)) if m else None
            if temp is None:
                continue
            util, mem = as_int(m.group(3)), as_int(m.group(4))
            status = gpu_status(node_state, node_idle, util, mem)
            rows.append({
                "node": node, "node_state": node_state, "gpu": int(m.group(1)),
                "temp": temp, "util": "" if util is None else util,
                "mem_mib": "" if mem is None else mem,
                "status": status, "trigger": triggers(temp, status),
            })
            seen += 1
        if seen == 0:
            first = blocks["DMON"][0] if blocks["DMON"] else "no dcgmi output"
            no_data[node] = first.strip()[:80]
    return rows, unreachable, no_data, no_state


def write_csv(name, data):
    with open(os.path.join(out_dir, name), "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(data)


def print_table(flagged):
    head = ("NODE", "SLURM STATE", "GPU", "TEMP", "UTIL", "MEM MiB", "GPU STATUS", "WOULD TRIGGER")
    order = sorted(flagged, key=lambda r: (-("CEILING" in r["trigger"]), -r["temp"], r["node"], r["gpu"]))
    body = [(r["node"], r["node_state"], str(r["gpu"]), f'{r["temp"]}C',
             "n/a" if r["util"] == "" else f'{r["util"]}%',
             "n/a" if r["mem_mib"] == "" else str(r["mem_mib"]),
             r["status"], r["trigger"]) for r in order]
    widths = [max(len(h), *(len(row[i]) for row in body)) for i, h in enumerate(head)]
    line = "  ".join("{:<%d}" % w for w in widths)
    print(line.format(*head))
    print(line.format(*("-" * w for w in widths)))
    for row in body:
        print(line.format(*row))


def print_per_node(flagged, flagged_nodes):
    by_node = collections.defaultdict(list)
    for r in flagged:
        by_node[r["node"]].append(r)
    print("\nPer node:")
    for node in flagged_nodes:
        gpus = by_node[node]
        detail = ", ".join(f'GPU{r["gpu"]} {r["temp"]}C {r["status"]} [{r["trigger"]}]' for r in gpus)
        print(f"  {node} ({gpus[0]['node_state']}): {len(gpus)} GPU(s) - {detail}")


def print_list(title, mapping):
    print(f"\n{title}")
    for node, message in mapping.items():
        print(f"  {node}: {message}")


nodes = read_nodes(nodes_file)
rows, unreachable, no_data, no_state = scan(nodes)
flagged = [r for r in rows if r["trigger"]]
flagged_nodes = sorted({r["node"] for r in flagged})
ceiling_nodes = {r["node"] for r in flagged if "CEILING" in r["trigger"]}
idle_nodes = {r["node"] for r in flagged if "IDLE_HIGH" in r["trigger"]}

write_csv("all_gpus.csv", rows)
write_csv("flagged.csv", flagged)

print(f"\nRules: CEILING > {CEILING}C (any GPU, any node state)   IDLE_HIGH > {IDLE_MAX}C "
      f"(IDLE node, GPU 0% util and <= {IDLE_MEM_MAX} MiB in use; NHC drains after {WINDOW}m if still hot)")
print(f"Nodes in list: {len(nodes)}   scanned OK: {len({r['node'] for r in rows})}   "
      f"unreachable: {len(unreachable)}   no dcgmi data: {len(no_data)}")
print(f"Nodes flagged: {len(flagged_nodes)}   (CEILING: {len(ceiling_nodes)}, IDLE_HIGH: {len(idle_nodes)})")
print(f"GPUs flagged:  {len(flagged)} of {len(rows)} read\n")

if flagged:
    print_table(flagged)
    print_per_node(flagged, flagged_nodes)
else:
    print("No node would be flagged right now.")

if unreachable:
    print_list("Unreachable:", unreachable)
if no_data:
    print_list("Reached but no GPU readings (dcgmi missing or failing):", no_data)
if no_state:
    print("\nSlurm node state not readable (idle rule not evaluated): " + ", ".join(no_state))
print(f"\nFiles: {out_dir}/flagged.csv  {out_dir}/all_gpus.csv  (raw output in {out_dir}/raw/)")
print("Note: IDLE_HIGH is a snapshot. NHC only drains if the GPU is still idle and hot after the window.")
PY
}

main() {
    load_settings "$@"
    preflight
    collect_all
    summarize
}

main "$@"
