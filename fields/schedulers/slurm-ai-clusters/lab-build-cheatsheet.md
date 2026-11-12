---
id: slurm-lab-cheatsheet
title: "Lab Build Cheatsheet: A Slurm AI Cluster in Containers"
sidebar_label: "6. Lab build cheatsheet"
order: 6
summary: Every step used to build the Slurm lab behind the pending-jobs and AI-cluster series - node image, Slurm 23.11 with accounting, topology, PyTorch, Enroot and Pyxis, health check, Slurm 26.05, metrics.
level: intermediate
type: [reference, guide]
domains: [systems-and-hpc]
tags: [slurm, hpc, containers]
relations:
  related: [slurm-topology-placement, slurm-distributed-training, slurm-containers-pyxis, slurm-gpu-health-checks, slurm-openmetrics, slurm-pending-reasons]
---

# Lab Build Cheatsheet: A Slurm AI Cluster in Containers

> **Part 6 of [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md)**, and the lab behind [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md) too. Direct steps, in order, to build the same cluster on one Linux machine: one controller, four CPU nodes, one node with four fake GPUs, and a second small cluster on Slurm 26.05.

- [What you get](#what-you-get)
- [0. The host](#0-the-host)
- [1. The node image](#1-the-node-image)
- [2. Start the containers](#2-start-the-containers)
- [3. Munge, names and users](#3-munge-names-and-users)
- [4. Slurm 23.11 with accounting](#4-slurm-2311-with-accounting)
- [5. Accounts, QOS and limits](#5-accounts-qos-and-limits)
- [6. Topology variants](#6-topology-variants)
- [7. PyTorch](#7-pytorch)
- [8. Containers: Enroot and Pyxis](#8-containers-enroot-and-pyxis)
- [9. GPU health check](#9-gpu-health-check)
- [10. Slurm 26.05 from source](#10-slurm-2605-from-source)
- [11. Metrics into VictoriaMetrics](#11-metrics-into-victoriametrics)
- [When the lab breaks](#when-the-lab-breaks)
- [References](#references)

> [!NOTE]
> Every command here was run while building the lab for these pages, on an Ubuntu 24.04 host. They're collected from several sessions into one order; the whole sequence was **not** re-run from an empty machine in one go. Lab-only shortcuts (privileged containers, a password in a config file, world-writable directories) are marked. Don't copy them into production.

---

## What you get

| Host | IP | Role |
| --- | --- | --- |
| `head01` | 10.10.0.10 | slurmctld, slurmdbd, MariaDB, login node |
| `cn001`–`cn004` | 10.10.0.11–14 | CPU nodes, partition `cpu`, 2 CPUs each |
| `gpu001` | 10.10.0.21 | partition `gpu`, four fake GPUs (`/dev/nvidia0`–`3`) |
| `s26a`–`s26c` | 10.10.0.31–33 | Slurm 26.05.6 from source; `s26a` also runs slurmctld |

Versions: Slurm 23.11.4 (Ubuntu packages) and 26.05.6, MariaDB 10.11, PyTorch 2.15.0, Enroot v4.2.1 tag, Pyxis v0.24.0, VictoriaMetrics v1.156.0.

---

## 0. The host

You need Docker, `debootstrap`, about 20 GB of free disk (PyTorch alone is 5.3 GB), and cgroup access for systemd in containers. Our host was cgroup v1 (hybrid); the nodes' `cgroup.conf` uses `CgroupPlugin=autodetect`.

```bash
apt-get install -y docker.io debootstrap
docker network create --subnet 10.10.0.0/24 cluster
```

---

## 1. The node image

One Ubuntu 24.04 root filesystem with everything any node needs, imported as a Docker image that boots systemd:

```bash
debootstrap noble /srv/rootfs http://archive.ubuntu.com/ubuntu
mount --bind /proc /srv/rootfs/proc; mount --bind /dev /srv/rootfs/dev
chroot /srv/rootfs bash -c '
  echo "deb http://archive.ubuntu.com/ubuntu noble main universe
deb http://archive.ubuntu.com/ubuntu noble-updates main universe" > /etc/apt/sources.list
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    systemd systemd-sysv dbus openssh-server sudo iproute2 python3 python3-venv python3-pip \
    munge slurm-wlm slurmdbd mariadb-server libpam-slurm-adopt libpam-systemd \
    libslurm-dev build-essential curl jq ca-certificates \
    squashfs-tools squashfuse fuse-overlayfs parallel pigz zstd bsdextrautils busybox-static
  useradd -m -s /bin/bash -u 1000 admin
  echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin
  systemctl enable ssh munge'
install -d -m 700 /srv/rootfs/home/admin/.ssh
cp ~/.ssh/id_ed25519.pub /srv/rootfs/home/admin/.ssh/authorized_keys     # Ansible logs in as admin
chroot /srv/rootfs chown -R admin:admin /home/admin/.ssh
umount /srv/rootfs/dev /srv/rootfs/proc

tar -C /srv/rootfs -c . | docker import -c 'CMD ["/sbin/init"]' -c 'ENV container=docker' - acot/node:noble-systemd
```

`bsdextrautils` is in the list because Enroot needs `column` for named containers; leaving it out cost us a failed test ([part 3](/fields/schedulers/slurm-ai-clusters/containers-with-pyxis.md#installing-and-the-dependencies-nobody-lists)).

---

## 2. Start the containers

`~/alab/lab.sh`, which starts, stops or rebuilds the six main nodes:

```bash
#!/bin/bash
# lab.sh up | down | reinstall <node>   -- fake cluster: head01, cn001-cn004, gpu001
declare -A IP=([head01]=10.10.0.10 [cn001]=10.10.0.11 [cn002]=10.10.0.12 [cn003]=10.10.0.13 [cn004]=10.10.0.14 [gpu001]=10.10.0.21)
start(){ docker run -d --restart unless-stopped --privileged --ulimit nofile=1024:20000 --name $1 --hostname $1 --network cluster --ip ${IP[$1]} \
  --cgroupns=host -v /sys/fs/cgroup:/sys/fs/cgroup:rw --tmpfs /run --tmpfs /run/lock acot/node:noble-systemd >/dev/null; }
case $1 in
  up) for n in "${!IP[@]}"; do start $n; done; sleep 8
      for n in "${!IP[@]}"; do printf "%s %s\n" $n "$(docker exec $n systemctl is-system-running)"; done | sort ;;
  down) docker rm -f "${!IP[@]}" >/dev/null 2>&1 ;;
  reinstall) docker rm -f $2 >/dev/null; start $2; sleep 8; echo "$2 reinstalled (new host keys)" ;;
esac
```

```bash
~/alab/lab.sh up
```

`--privileged` is a lab shortcut: systemd, cgroups and `mknod` for the fake GPUs need it.

---

## 3. Munge, names and users

```bash
# One munge key for every node (and later the 26.05 nodes)
dd if=/dev/urandom bs=1 count=1024 of=/tmp/munge.key 2>/dev/null
for n in head01 cn001 cn002 cn003 cn004 gpu001; do
  docker cp /tmp/munge.key $n:/etc/munge/munge.key
  docker exec $n bash -c 'chown munge:munge /etc/munge/munge.key; chmod 400 /etc/munge/munge.key; systemctl restart munge'
done

# The host resolves the nodes by name (Ansible connects over SSH)
cat >> /etc/hosts <<'EOF'
10.10.0.10 head01
10.10.0.11 cn001
10.10.0.12 cn002
10.10.0.13 cn003
10.10.0.14 cn004
10.10.0.21 gpu001
EOF

# Test users, same UIDs on every node
for n in head01 cn001 cn002 cn003 cn004 gpu001; do
  docker exec $n bash -c 'useradd -m -u 2001 alice; useradd -m -u 2002 bob; useradd -m -u 2003 carol'
done
```

We distributed the key with the `munge` role from the [Ansible series](/fields/devops/ansible/README.md); `docker cp` does the same in a lab.

---

## 4. Slurm 23.11 with accounting

The configuration is an Ansible project, `~/slurmlab`, with the inventory groups `head` (head01) and `nodes` (cn001–cn004, gpu001):

```text
~/slurmlab/
├── ansible.cfg          # inventory, remote_user = admin
├── site.yml
└── templates/
    ├── slurm.conf.j2
    ├── slurmdbd.conf.j2
    ├── cgroup.conf.j2
    └── gres.conf.j2
```

`templates/slurm.conf.j2`:

```text
ClusterName=lab
SlurmctldHost=head01
SlurmUser=slurm
AuthType=auth/munge
MpiDefault=none
ProctrackType=proctrack/cgroup
TaskPlugin=task/cgroup
PrologFlags=contain
JobAcctGatherType=jobacct_gather/cgroup
SelectType=select/cons_tres
SelectTypeParameters=CR_Core_Memory
ReturnToService=2
StateSaveLocation=/var/lib/slurm/slurmctld
SlurmdSpoolDir=/var/lib/slurm/slurmd
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
GresTypes=gpu
AccountingStorageType=accounting_storage/slurmdbd
AccountingStorageHost=head01
AccountingStorageEnforce=associations,limits,qos,safe
AccountingStorageTRES=gres/gpu
JobCompType=jobcomp/none
SchedulerType=sched/backfill
SchedulerParameters=bf_interval=10
PriorityType=priority/multifactor
PriorityWeightAge={{ prio_age | default(1000) }}
PriorityWeightFairshare={{ prio_fairshare | default(10000) }}
PriorityWeightJobSize={{ prio_jobsize | default(0) }}
PriorityWeightPartition={{ prio_partition | default(0) }}
PriorityWeightQOS={{ prio_qos | default(5000) }}
PriorityMaxAge={{ prio_maxage | default("1-0") }}
PriorityDecayHalfLife=7-0
{{ extra_slurm_conf | default('') }}

NodeName=cn[001-004] CPUs=2 RealMemory=3000 State=UNKNOWN
NodeName=gpu001 CPUs=2 RealMemory=3000 Gres=gpu:h100:4 State=UNKNOWN
PartitionName=cpu Nodes=cn[001-004] Default=YES MaxTime=2-00:00:00 State=UP
PartitionName=gpu Nodes=gpu001 MaxTime=2-00:00:00 QOS=gpu-normal State=UP
```

The `QOS=gpu-normal` on the `gpu` partition comes from [part 3 of the pending series](/fields/schedulers/slurm-pending-jobs/limits-that-wait-forever.md#closing-it-with-a-partition-qos). The QOS doesn't exist yet on the first run: leave `QOS=gpu-normal` out until step 5 has created it, then add it back and run the playbook again. Note there's no `DefMemPerCPU`: this lab shows the default that [part 5](/fields/schedulers/slurm-ai-clusters/metrics-openmetrics.md#the-two-numbers-that-explained-it) fixes.

`templates/slurmdbd.conf.j2` (installed mode 0600, owner slurm):

```text
AuthType=auth/munge
DbdHost=head01
SlurmUser=slurm
StorageType=accounting_storage/mysql
StorageHost=localhost
StorageUser=slurm
StoragePass=labonly
StorageLoc=slurm_acct_db
LogFile=/var/log/slurm/slurmdbd.log
PidFile=/run/slurmdbd/slurmdbd.pid
```

`templates/cgroup.conf.j2` and `templates/gres.conf.j2`:

```text
CgroupPlugin=autodetect
ConstrainCores=yes
ConstrainRAMSpace=yes
ConstrainDevices=yes
```

```text
NodeName=gpu001 Name=gpu Type=h100 File=/dev/nvidia[0-3]
```

`site.yml` does, in order: start MariaDB and create the `slurm_acct_db` database and `slurm` user; install `slurmdbd.conf` and start `slurmdbd`, waiting for port 6819; on every host, create the fake GPU device files on `gpu001` (`mknod -m 666 /dev/nvidia$i c 195 $i` for 0–3), create `/var/lib/slurm` and `/var/log/slurm`, template the three config files, install `topology.conf` only when the `topology_conf` variable is set (and remove it otherwise), restart what changed, then start `slurmctld` on the head and `slurmd` on the nodes.

```bash
cd ~/slurmlab
ANSIBLE_CONFIG=$PWD/ansible.cfg ansible-playbook site.yml \
  -e '{"extra_slurm_conf": "RebootProgram=/usr/sbin/reboot\nPriorityCalcPeriod=1"}'
docker exec head01 sinfo
```

Expected: partitions `cpu*` (4 nodes) and `gpu` (1 node), all `idle`.

---

## 5. Accounts, QOS and limits

On `head01`:

```bash
sacctmgr -i add account physics,chem
sacctmgr -i add user alice,bob,admin account=physics
sacctmgr -i add user carol account=chem
sacctmgr -i add qos gpu-normal MaxTRESPerUser=gres/gpu=2
sacctmgr -i modify qos gpu-normal set flags=DenyOnLimit
sacctmgr -i add qos urgent Priority=100
sacctmgr -i modify user alice,bob,carol,admin set qos+=gpu-normal
sacctmgr -i modify user carol set qos+=urgent
sacctmgr -i modify account physics set GrpTRES=gres/gpu=3
sacctmgr -n -P show assoc format=account,user,qos,grptres
```

```text
root||normal|
root|root|normal|
chem||normal|
chem|carol|gpu-normal,normal,urgent|
physics||normal|gres/gpu=3|
physics|admin|gpu-normal,normal|
physics|alice|gpu-normal,normal|
physics|bob|gpu-normal,normal|
```

The pending series' `whypending` script goes to `/usr/local/bin/whypending` on `head01`; it's printed in full in [part 1](/fields/schedulers/slurm-pending-jobs/why-is-my-job-pending.md#a-triage-script-and-the-bug-we-found-in-it).

---

## 6. Topology variants

Two variable files for `site.yml`. Tree (`/tmp/tree.yml`):

```yaml
topology_conf: |
  SwitchName=leaf1 Nodes=cn[001-002]
  SwitchName=leaf2 Nodes=cn[003-004]
  SwitchName=leaf3 Nodes=gpu001
  SwitchName=spine Switches=leaf[1-3]
extra_slurm_conf: |
  RebootProgram=/usr/sbin/reboot
  PriorityCalcPeriod=1
  TopologyPlugin=topology/tree
```

Block (`/tmp/block.yml`): every block the same size, and `gpu001` left out (a 1-node block next to 2-node blocks is fatal to `slurmctld`):

```yaml
topology_conf: |
  BlockName=nvl1 Nodes=cn[001-002]
  BlockName=nvl2 Nodes=cn[003-004]
extra_slurm_conf: |
  RebootProgram=/usr/sbin/reboot
  PriorityCalcPeriod=1
  TopologyPlugin=topology/block
```

```bash
ANSIBLE_CONFIG=$PWD/ansible.cfg ansible-playbook site.yml -e @/tmp/tree.yml
docker exec head01 scontrol show topology
```

Run `site.yml` without `-e @...` to go back to no topology. `extra_slurm_conf` replaces the whole block, so repeat any line you still want, such as the health check from step 9.

---

## 7. PyTorch

On the host, into the image's root filesystem (the shell there needs the proxy and CA settings if your network has them):

```bash
mount --bind /proc /srv/rootfs/proc; mount --bind /dev /srv/rootfs/dev
chroot /srv/rootfs bash -c 'python3 -m venv /opt/torchenv && /opt/torchenv/bin/pip install --no-cache-dir torch==2.15.0'
chroot /srv/rootfs /opt/torchenv/bin/python -c "import torch, torch.distributed as d; print(torch.__version__, d.is_gloo_available())"
umount /srv/rootfs/dev /srv/rootfs/proc
```

```text
2.15.0+cu132 True
```

The PyPI wheel pulls about 3 GB of NVIDIA libraries even for CPU use; `import torch` fails without them (`libcudart.so.13: cannot open shared object file`), so don't install with `--no-deps`. We added the venv to already-running containers; starting fresh, do this before the `docker import` in step 1, so `/opt/torchenv` is in the image.

Then put the test program from [part 2](/fields/schedulers/slurm-ai-clusters/launching-distributed-training.md#what-pytorch-needs-from-slurm) on the CPU nodes:

```bash
for n in cn001 cn002 cn003 cn004; do docker cp allreduce.py $n:/usr/local/share/allreduce.py; done
```

---

## 8. Containers: Enroot and Pyxis

Build in the image root (which has `libslurm-dev` 23.11.4 for Pyxis), then copy the results to the nodes that should have them. Enroot's musl submodule points at `git.musl-libc.org`; if your network can't reach it, point it at a mirror of the same commit.

```bash
mkdir -p /srv/rootfs/srv/build/ct && cd /srv/rootfs/srv/build/ct
git clone --depth 1 -b v4.2.1 --recurse-submodules https://github.com/NVIDIA/enroot
git clone --depth 1 -b v0.24.0 https://github.com/NVIDIA/pyxis
mount --bind /proc /srv/rootfs/proc; mount --bind /dev /srv/rootfs/dev
chroot /srv/rootfs bash -c '
  cd /srv/build/ct/enroot && make prefix=/usr/local sysconfdir=/etc -j4 &&
    make install prefix=/usr/local sysconfdir=/etc DESTDIR=/srv/stage
  cd /srv/build/ct/pyxis && make -j4'
umount /srv/rootfs/dev /srv/rootfs/proc
```

Pass the same `sysconfdir` to the build **and** the install. We built without it, and Enroot looked for its hooks in `/usr/local/etc/enroot` instead of `/etc/enroot` ([part 3](/fields/schedulers/slurm-ai-clusters/containers-with-pyxis.md#installing-and-the-dependencies-nobody-lists)); the lab fixed it with `ln -s /etc/enroot /usr/local/etc/enroot` on each node. The build line above is the corrected form, not re-run.

On `head01`, `cn001` and `cn002` (leave `cn003` without, to reproduce part 3's story):

```bash
R=/srv/rootfs/srv
for n in head01 cn001 cn002; do
  docker cp $R/stage/. $n:/
  docker exec $n mkdir -p /usr/local/lib/slurm
  docker cp $R/build/ct/pyxis/spank_pyxis.so $n:/usr/local/lib/slurm/spank_pyxis.so
  docker exec $n bash -c '
    echo "required /usr/local/lib/slurm/spank_pyxis.so container_scope=job" > /etc/slurm/plugstack.conf
    cat > /etc/enroot/enroot.conf.d/10-paths.conf <<"EOF"
ENROOT_RUNTIME_PATH /run/enroot/user-$(id -u)
ENROOT_CACHE_PATH   /var/lib/enroot/cache/user-$(id -u)
ENROOT_DATA_PATH    /var/lib/enroot/data/user-$(id -u)
EOF
    mkdir -p /run/enroot /var/lib/enroot/cache /var/lib/enroot/data
    chmod 1777 /run/enroot /var/lib/enroot/cache /var/lib/enroot/data      # lab shortcut
    echo "d /run/enroot 1777 root root -" > /etc/tmpfiles.d/enroot.conf
    cp /usr/local/share/enroot/hooks.d/50-slurm-pytorch.sh /etc/enroot/hooks.d/
    systemctl restart slurmd 2>/dev/null; enroot version'
done
docker exec head01 bash -c 'srun --help | grep -c container'    # > 0: Pyxis is loaded
```

The test images, a busybox root with an `os-release`, one with `PYTORCH_VERSION` set for the hook:

```bash
chroot /srv/rootfs bash -c '
  mkdir -p /srv/img/{bin,etc,tmp,proc,sys,dev,home,run,root,data} && chmod 1777 /srv/img/tmp
  cp /bin/busybox /srv/img/bin/
  for c in sh ls cat hostname id grep env echo nproc df; do ln -sf busybox /srv/img/bin/$c; done
  echo "PRETTY_NAME=\"acot lab image 1.0\"" > /srv/img/etc/os-release
  mksquashfs /srv/img /srv/labimg.sqsh -noappend -quiet
  cp -a /srv/img /srv/img2 && echo "PYTORCH_VERSION=2.15.0" > /srv/img2/etc/environment
  mksquashfs /srv/img2 /srv/ptimg.sqsh -noappend -quiet'
for n in head01 cn001 cn002 cn003; do
  docker cp /srv/rootfs/srv/labimg.sqsh $n:/srv/labimg.sqsh
  docker cp /srv/rootfs/srv/ptimg.sqsh $n:/srv/ptimg.sqsh
done
docker exec head01 su alice -c 'cd /tmp; srun -p cpu -N2 --container-image=/srv/labimg.sqsh grep PRETTY /etc/os-release'
```

Expected: `PRETTY_NAME="acot lab image 1.0"` twice.

---

## 9. GPU health check

The script is in [part 4](/fields/schedulers/slurm-ai-clusters/gpu-health-checks.md#a-gpu-health-check). Copy it to every node, then add it to `slurm.conf`:

```bash
for n in cn001 cn002 cn003 cn004 gpu001; do docker cp gpu-health $n:/usr/local/sbin/gpu-health; done
ANSIBLE_CONFIG=$PWD/ansible.cfg ansible-playbook site.yml -e '{"extra_slurm_conf":
  "RebootProgram=/usr/sbin/reboot\nPriorityCalcPeriod=1\nHealthCheckProgram=/usr/local/sbin/gpu-health\nHealthCheckInterval=30"}'
```

Test: `docker exec gpu001 rm /dev/nvidia2`, wait 30 s, `sinfo -R`. Put it back with `docker exec gpu001 mknod -m 666 /dev/nvidia2 c 195 2` and `scontrol update nodename=gpu001 state=resume`.

---

## 10. Slurm 26.05 from source

A separate build root, so the main image keeps its Ubuntu Slurm packages:

```bash
debootstrap noble /srv/build http://archive.ubuntu.com/ubuntu
# add "universe" to /srv/build/etc/apt/sources.list as in step 1, then:
chroot /srv/build bash -c 'apt-get update && apt-get install -y build-essential libmunge-dev libjson-c-dev \
  libhttp-parser-dev libyaml-dev libjwt-dev libpam0g-dev libmariadb-dev libdbus-1-dev liblz4-dev libreadline-dev libssl-dev'
git clone --depth 1 -b slurm-26-05-6-1 https://github.com/SchedMD/slurm /srv/build/usr/src/slurm-26.05.6
chroot /srv/build bash -c 'cd /usr/src/slurm-26.05.6 &&
  ./configure --prefix=/opt/slurm26 --sysconfdir=/opt/slurm26/etc --with-munge --with-json --with-http-parser --with-yaml &&
  make -j2 && make install && echo BUILD-OK'
```

`--with-http-parser` and `--with-yaml` matter: the OpenMetrics endpoints and `topology.yaml` need them. The runtime libraries (`libhttp-parser2.9`, `libjwt2`) were already in the node image.

Image and containers:

```bash
cp -a /srv/build/opt/slurm26 /srv/rootfs/opt/
tar -C /srv/rootfs -c . | docker import -c 'CMD ["/sbin/init"]' -c 'ENV container=docker' - acot/node:noble-s26
for i in a:31 b:32 c:33; do n=s26${i%%:*}; ip=10.10.0.${i##*:}
  docker run -d --restart unless-stopped --privileged --ulimit nofile=1024:20000 --name $n --hostname $n \
    --network cluster --ip $ip --cgroupns=host -v /sys/fs/cgroup:/sys/fs/cgroup:rw --tmpfs /run --tmpfs /run/lock acot/node:noble-s26
done
```

Copy `/tmp/munge.key` in and restart munge as in step 3, then on each: `mkdir -p /var/lib/slurm26 /var/log/slurm26 && chown slurm:slurm /var/lib/slurm26 /var/log/slurm26`. `/opt/slurm26/etc/slurm.conf` on all three:

```text
ClusterName=lab26
SlurmctldHost=s26a
SlurmUser=slurm
AuthType=auth/munge
MpiDefault=none
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
SelectType=select/cons_tres
ReturnToService=2
StateSaveLocation=/var/lib/slurm26/ctld
SlurmdSpoolDir=/var/lib/slurm26/d
SlurmctldLogFile=/var/log/slurm26/slurmctld.log
SlurmdLogFile=/var/log/slurm26/slurmd.log
SlurmctldPidFile=/run/slurmctld26.pid
SlurmdPidFile=/run/slurmd26.pid
MetricsType=metrics/openmetrics
NodeName=s26a,s26b,s26c CPUs=2 RealMemory=1000 State=UNKNOWN
PartitionName=all Nodes=s26a,s26b,s26c Default=YES MaxTime=1-00:00:00 State=UP
PartitionName=nvl Nodes=s26a,s26b Topology=nvl MaxTime=1-00:00:00 State=UP
```

(Add `DefMemPerCPU=400` after reproducing the part 5 story.) Node names are listed one by one: `s26[a-c]` isn't a valid range, Slurm ranges are numeric. `/opt/slurm26/etc/topology.yaml` is in [part 1](/fields/schedulers/slurm-ai-clusters/topology-aware-placement.md#two-topologies-in-one-cluster-2505).

Start the daemons once munge is running. Use `docker exec -d`; a background `&` inside `docker exec bash -c` died with the exec session:

```bash
docker exec -d s26a /opt/slurm26/sbin/slurmctld -f /opt/slurm26/etc/slurm.conf
for n in s26a s26b s26c; do docker exec -d $n /opt/slurm26/sbin/slurmd -f /opt/slurm26/etc/slurm.conf; done
docker exec s26a bash -c 'SLURM_CONF=/opt/slurm26/etc/slurm.conf /opt/slurm26/bin/sinfo'
curl -s http://10.10.0.31:6817/metrics
```

Expected: partitions `all*` and `nvl`, and the index of five metrics endpoints.

---

## 11. Metrics into VictoriaMetrics

VictoriaMetrics single-node as in [its series](/fields/devops/victoriametrics/single-node-in-ten-minutes.md), with the scrape file from [part 5](/fields/schedulers/slurm-ai-clusters/metrics-openmetrics.md#scraping-it):

```bash
victoria-metrics-prod -storageDataPath=/root/vmlab/t12/data -httpListenAddr=127.0.0.1:8428 \
  -promscrape.config=/root/vmlab/t12/scrape.yml
curl -s 'http://127.0.0.1:8428/api/v1/query' --data-urlencode 'query=up{job=~"slurm.*"}'
vmalert-tool-prod unittest --files slurm-rules.test.yml
```

Expected: three `up` series with value `1`, and `SUCCESS`.

---

## When the lab breaks

| Symptom | Cause | Fix |
| --- | --- | --- |
| `docker` commands hang or the daemon is gone | `dockerd` was started from a shell that ended | `setsid -f dockerd > /tmp/dockerd.log 2>&1 < /dev/null` |
| After a Docker restart, `gpu001` is `down*` | `/dev/nvidia*` don't survive a container restart | Re-run `site.yml` (step 4) |
| Ansible: `UNREACHABLE` | `/etc/hosts` lost the node names | Re-add the lines from step 3 |
| Ansible: `Attempting to decrypt but no vault secrets found` | The inventory has vault-encrypted vars | `vault_password_file` in `ansible.cfg` |
| 26.05 daemons: `auth/munge` fatal | Started before munge | `systemctl restart munge`, then start them again |
| `slurmctld` exits after a topology change | Unequal block sizes | See step 6 |
| `scontrol reboot` leaves nodes in `reboot^` | Containers report the host's boot time | Lab artifact; `scontrol update nodename=... state=resume` ([reboot order](/fields/schedulers/slurm-reboot-order.md)) |
| `scancel -u alice -u bob` cancels only bob's jobs | Only the last `-u` counts | Loop: `for u in alice bob; do scancel -u $u; done` |

Teardown: `~/alab/lab.sh down`, then `docker rm -f s26a s26b s26c`.

**Takeaway:** the whole lab is one Ubuntu root filesystem imported as a systemd image, six plus three privileged containers on one Docker network, and an Ansible playbook for Slurm; everything after that is a few files copied onto the nodes.

**Series index:** [Slurm for AI Clusters](/fields/schedulers/slurm-ai-clusters/README.md). For what this lab was used to show about the queue, see [Why Is My Job Still Pending?](/fields/schedulers/slurm-pending-jobs/README.md).

---

## References

- [Slurm: Quick Start Administrator Guide](https://slurm.schedmd.com/quickstart_admin.html): building from source, `configure` options, daemons.
- [Slurm: Accounting](https://slurm.schedmd.com/accounting.html): slurmdbd and MariaDB setup.
- [MUNGE installation guide](https://github.com/dun/munge/wiki/Installation-Guide): one key on every node.
- [Enroot: installation](https://github.com/NVIDIA/enroot/blob/master/doc/installation.md) and [Pyxis](https://github.com/NVIDIA/pyxis): building from source.
- [debootstrap(8)](https://manpages.ubuntu.com/manpages/noble/man8/debootstrap.8.html) and [docker import](https://docs.docker.com/reference/cli/docker/image/import/): building the node image.
- [PyTorch on PyPI](https://pypi.org/project/torch/): the wheel and its NVIDIA dependencies.
