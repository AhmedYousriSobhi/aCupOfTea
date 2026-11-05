#!/usr/bin/env python3
"""nhc_gen.py -- generate LBNL NHC configs from a cluster architecture definition.

Usage:
    nhc_gen.py cluster.yaml --out build/ [--slurm-conf /etc/slurm/slurm.conf] [--strict]

Writes:
    build/nhc.conf          periodic checks (HealthCheckProgram)
    build/nhc-epilog.conf   fast post-job checks
    build/nhc-deep.conf     periodic checks + slow diagnostics
    build/sysconfig/<ctx>   early settings (NHC_RM, TIMEOUT) per context

Exits non-zero if the definition is inconsistent, or disagrees with slurm.conf.
Requires: Python 3.8+, PyYAML.  Part of the aCupOfTea NHC series (part 9).
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

import yaml

# How a service name in the YAML maps to a process: (owner, daemon binary)
SERVICE_MAP = {
    "sshd": ("root", "sshd"),
    "munge": ("munge", "munged"),
    "chronyd": ("chrony", "chronyd"),
}

CONTEXTS = ("nhc", "nhc-epilog", "nhc-deep")
UNITS_KB = {"KB": 1, "K": 1, "MB": 1024, "M": 1024, "GB": 1024**2, "G": 1024**2,
            "TB": 1024**3, "T": 1024**3}


class Problems:
    """Collects errors and warnings so the user sees all of them in one run."""

    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


# --------------------------------------------------------------------------- hostlists
def split_top_level(expr):
    """'a[1-3,5],b' -> ['a[1-3,5]', 'b']: split on commas outside brackets."""
    parts, depth, cur = [], 0, ""
    for ch in expr:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


HOST_RE = re.compile(r"^([^\[\]]*)\[([^\[\]]+)\]([^\[\]]*)$")


def expand_hostlist(expr):
    """Expand Slurm-style hostlists with one bracket group per name."""
    hosts = []
    for item in split_top_level(expr):
        m = HOST_RE.match(item)
        if "[" not in item:
            hosts.append(item)
            continue
        if not m:
            raise ValueError(f"unsupported hostlist (one [...] group per name): {item!r}")
        prefix, body, suffix = m.groups()
        for rng in body.split(","):
            if "-" in rng:
                lo, hi = rng.split("-", 1)
                width = len(lo)
                for n in range(int(lo), int(hi) + 1):
                    hosts.append(f"{prefix}{n:0{width}d}{suffix}")
            else:
                hosts.append(f"{prefix}{rng}{suffix}")
    return hosts


def nhc_target(expr):
    """Slurm hostlist -> NHC node-range match string.

    NHC allows one range per name and no commas inside brackets, so
    'cn[001-010,015]' becomes '{cn[001-010],cn015}'.
    """
    out = []
    for item in split_top_level(expr):
        m = HOST_RE.match(item)
        if not m:
            out.append(item)
            continue
        prefix, body, suffix = m.groups()
        for rng in body.split(","):
            out.append(f"{prefix}[{rng}]{suffix}" if "-" in rng else f"{prefix}{rng}{suffix}")
    return "{" + ",".join(out) + "}"


# --------------------------------------------------------------------------- helpers
def size_kb(text):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([KMGT]B?)\s*", str(text), re.I)
    if not m:
        raise ValueError(f"bad size {text!r} (use e.g. 512GB, 2TB)")
    return int(float(m.group(1)) * UNITS_KB[m.group(2).upper()])


def mount_check(fs):
    kind = "check_fs_mount_ro" if fs.get("read_only") else "check_fs_mount_rw"
    return f"{kind} -t {fs['type']} -s '{fs['source']}' -f {fs['mountpoint']}"


def xid_check(xids):
    codes = "|".join(str(x) for x in sorted(set(xids)))
    return (f"check_cmd_dmesg -m '!/NVRM: Xid [(]PCI:[^)]*[)]: ({codes}),/' "
            f"-M 'Fatal GPU Xid in kernel log'")


# --------------------------------------------------------------------------- validation
def validate(spec, p):
    for key in ("cluster", "classes"):
        if key not in spec:
            p.error(f"missing top-level key '{key}'")
    storage = spec.get("storage", {})
    fabrics = spec.get("fabrics", {})
    roles = spec.get("roles", {})
    owner = {}  # host -> class, to catch overlaps

    for name, cls in spec.get("classes", {}).items():
        where = f"class '{name}'"
        try:
            hosts = expand_hostlist(cls["nodes"])
        except (KeyError, ValueError) as exc:
            p.error(f"{where}: nodes: {exc}")
            continue
        cls["_hosts"] = hosts
        for h in hosts:
            if h in owner:
                p.error(f"{where}: node {h} is also in class '{owner[h]}'")
            owner[h] = name

        if cls.get("role") not in roles:
            p.error(f"{where}: unknown role {cls.get('role')!r}")
        for m in cls.get("mounts", []):
            if m not in storage:
                p.error(f"{where}: unknown mount {m!r}")
        if cls.get("fabric") and cls["fabric"] not in fabrics:
            p.error(f"{where}: unknown fabric {cls['fabric']!r}")
        cpu = cls.get("cpu")
        if cpu and not (cpu["sockets"] <= cpu["cores"] <= cpu["threads"]):
            p.error(f"{where}: cpu must satisfy sockets <= cores <= threads")
        try:
            cls["_mem_kb"] = size_kb(cls["memory"]) if "memory" in cls else None
        except ValueError as exc:
            p.error(f"{where}: {exc}")
        gpus = cls.get("gpus")
        if gpus and int(gpus.get("count", 0)) < 1:
            p.error(f"{where}: gpus.count must be >= 1")

    for role, r in roles.items():
        for svc in r.get("services", []):
            if svc not in SERVICE_MAP:
                p.error(f"role '{role}': no SERVICE_MAP entry for service {svc!r}")
    return owner


# --------------------------------------------------------------------------- slurm.conf
def parse_slurm_nodes(path):
    """Return {host: {Sockets, CoresPerSocket, ThreadsPerCore, RealMemory, Gres}}."""
    text = Path(path).read_text().replace("\\\n", " ")
    defaults, nodes = {}, {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line.lower().startswith("nodename="):
            continue
        kv = dict(tok.split("=", 1) for tok in line.split() if "=" in tok)
        kv = {k.lower(): v for k, v in kv.items()}
        names = kv.pop("nodename")
        if names.upper() == "DEFAULT":
            defaults.update(kv)
            continue
        merged = {**defaults, **kv}
        for h in expand_hostlist(names):
            nodes[h] = merged
    return nodes


def gres_gpus(gres):
    total = 0
    for item in (gres or "").split(","):
        f = item.split(":")
        if f[0] == "gpu" and f[-1].split("(")[0].isdigit():
            total += int(f[-1].split("(")[0])
    return total


def cross_check_slurm(spec, owner, slurm_nodes, p):
    def short(hosts, n=8):
        hosts = sorted(hosts)
        return ", ".join(hosts[:n]) + (f" ... (+{len(hosts) - n} more)" if len(hosts) > n else "")

    uncovered = set(slurm_nodes) - set(owner)
    if uncovered:
        p.error(f"slurm.conf: {len(uncovered)} node(s) not covered by any class, "
                f"so they get no health checks: {short(uncovered)}")
    unknown = set(owner) - set(slurm_nodes)
    if unknown:
        p.warn(f"{len(unknown)} node(s) defined in classes but not in slurm.conf: {short(unknown)}")

    reported = set()  # one message per (class, problem), not per node
    for host, cls_name in owner.items():
        s = slurm_nodes.get(host)
        if s is None:
            continue
        cls = spec["classes"][cls_name]

        def report(kind, msg, level="error"):
            if (cls_name, kind) not in reported:
                reported.add((cls_name, kind))
                getattr(p, level)(f"class '{cls_name}' vs slurm.conf ({host} and others): {msg}")

        cpu = cls.get("cpu")
        if cpu and "sockets" in s:
            sockets = int(s["sockets"])
            cores = sockets * int(s.get("corespersocket", 1))
            threads = cores * int(s.get("threadspercore", 1))
            if (sockets, cores, threads) != (cpu["sockets"], cpu["cores"], cpu["threads"]):
                report("cpu", f"slurm says {sockets}/{cores}/{threads} sockets/cores/threads, "
                              f"architecture says {cpu['sockets']}/{cpu['cores']}/{cpu['threads']}")
        if cls.get("_mem_kb") and "realmemory" in s:
            real_mb, arch_mb = int(s["realmemory"]), cls["_mem_kb"] // 1024
            if real_mb > arch_mb:
                report("mem", f"RealMemory={real_mb} MB exceeds the {arch_mb} MB the node has; "
                              "Slurm will drain it as 'Low RealMemory'")
            elif real_mb < 0.85 * arch_mb:
                report("memlow", f"RealMemory={real_mb} MB hides >15% of {arch_mb} MB from jobs", "warn")
        want = int(cls.get("gpus", {}).get("count", 0))
        have = gres_gpus(s.get("gres"))
        if want != have:
            report("gpu", f"Gres has {have} GPUs, architecture says {want}")


# --------------------------------------------------------------------------- emitters
def class_lines(spec, cls, context):
    """Yield check lines for one class in one context, cheapest first."""
    storage, fabrics = spec.get("storage", {}), spec.get("fabrics", {})
    role = spec["roles"][cls["role"]]
    gpus = cls.get("gpus")
    fudge = spec.get("defaults", {}).get("memory_fudge", "3%")

    # mounts first: the #1 black-hole cause, and cheap (reads /proc/mounts)
    for m in cls.get("mounts", []):
        yield mount_check(storage[m])
    if gpus:
        yield f"check_arch_gpu_count {gpus['count']}"
        yield xid_check(gpus.get("fatal_xids", [48, 79]))
    if context == "nhc-epilog":
        return  # epilog stays tiny: every second here is added to every job

    for svc in role.get("services", []):
        user, daemon = SERVICE_MAP[svc]
        yield f"check_ps_service -u {user} -d {daemon} -S {svc}"
    if cls.get("cpu"):
        c = cls["cpu"]
        yield f"check_hw_cpuinfo {c['sockets']} {c['cores']} {c['threads']}"
    if cls.get("numa_nodes"):
        yield f"check_arch_numa_nodes {cls['numa_nodes']}"
    if cls.get("memory"):
        yield f"check_hw_physmem {cls['memory']} {cls['memory']} {fudge}"
    if cls.get("fabric"):
        fab = fabrics[cls["fabric"]]
        for dev in fab["devices"]:
            yield f"check_hw_ib {fab['rate']} {dev}"
    if gpus and gpus.get("model"):
        yield f"check_arch_gpu_model '{gpus['model']}'"
    if role.get("user_hygiene"):
        yield "check_ps_unauth_users log syslog"
        yield "check_ps_userproc_lineage log syslog"
    if context == "nhc-deep" and gpus:
        level = gpus.get("deep_diag_level", 2)
        yield f"check_arch_dcgm_diag {level} 600"


def render(spec, context, source_digest):
    out = [
        "#" * 78,
        f"# {context}.conf for cluster '{spec['cluster']}' -- GENERATED by nhc_gen.py.",
        f"# Source sha256:{source_digest[:16]}. Do not edit: change the YAML and regenerate.",
        "#" * 78,
        "",
        "### Global",
        '* || DF_FLAGS="-Tkal"',
        '* || DFI_FLAGS="-Tial"',
        "* || check_fs_mount_rw -f /",
    ]
    if context != "nhc-epilog":
        for target in spec.get("defaults", {}).get("ping_targets", []):
            out.append(f"* || check_net_ping -W 2 -c 2 {target}")

    for name, cls in spec["classes"].items():
        target = nhc_target(cls["nodes"])
        lines = list(class_lines(spec, cls, context))
        if not lines:
            continue
        out += ["", f"### class {name} ({len(cls['_hosts'])} nodes, role {cls['role']})"]
        width = len(target)
        out += [f"{target:>{width}} || {line}" for line in lines]
    return "\n".join(out) + "\n"


def render_sysconfig(spec, context):
    timeouts = spec.get("defaults", {}).get("timeouts", {})
    return (f"# /etc/sysconfig/{context} -- GENERATED by nhc_gen.py\n"
            f"NHC_RM=slurm\n"
            f"TIMEOUT={timeouts.get(context, 50)}\n")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec", help="cluster architecture YAML")
    ap.add_argument("--out", default="build", help="output directory")
    ap.add_argument("--slurm-conf", help="cross-check against this slurm.conf")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args()

    raw = Path(args.spec).read_bytes()
    spec = yaml.safe_load(raw)
    p = Problems()
    owner = validate(spec, p)
    if args.slurm_conf and not p.errors:
        cross_check_slurm(spec, owner, parse_slurm_nodes(args.slurm_conf), p)

    for w in p.warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in p.errors:
        print(f"ERROR:   {e}", file=sys.stderr)
    if p.errors or (args.strict and p.warnings):
        print("Nothing written.", file=sys.stderr)
        return 1

    out = Path(args.out)
    (out / "sysconfig").mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(raw).hexdigest()
    for ctx in CONTEXTS:
        (out / f"{ctx}.conf").write_text(render(spec, ctx, digest))
        (out / "sysconfig" / ctx).write_text(render_sysconfig(spec, ctx))
    print(f"OK: {len(owner)} nodes in {len(spec['classes'])} classes -> "
          f"{', '.join(c + '.conf' for c in CONTEXTS)} in {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
