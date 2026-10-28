---
id: nhc-build-and-install
title: Build and Install NHC
sidebar_label: "2. Build and install"
order: 2
summary: Get NHC onto your nodes from a release RPM, the release tarball or the Git tree, run its unit tests and know where every file lands.
level: beginner
type: guide
domains: [systems-and-hpc]
tags: [hpc]
relations:
  prerequisites: [nhc-why-node-health-check]
---

# Build and Install NHC

> **Part 2 of the [Node Health Check series](/fields/system-administration/node-health-check/README.md).** By the end of this page NHC is installed on a node, its 800-odd unit tests are green, and you know where every file lives.

## Table of Contents
- [Pick your route](#pick-your-route)
- [Before you start: the one trap everyone falls into](#before-you-start-the-one-trap-everyone-falls-into)
- [Route A: release RPM (RHEL, Rocky, Alma, Oracle)](#route-a-release-rpm-rhel-rocky-alma-oracle)
- [Route B: release tarball (any distro)](#route-b-release-tarball-any-distro)
- [Route C: straight from Git](#route-c-straight-from-git)
- [Where everything lands](#where-everything-lands)
- [Smoke test](#smoke-test)
- [Getting it onto 500 nodes](#getting-it-onto-500-nodes)

---

## Pick your route

| Route | Use it when | Effort |
|-------|-------------|--------|
| **A. Release RPM** | RHEL-family nodes and you just want the stable release | ☕ |
| **B. Release tarball** | Ubuntu/Debian, SUSE without OBS, or a custom prefix | ☕☕ |
| **C. Git tree** | You need an unreleased fix, or you plan to contribute | ☕☕☕ |

SUSE folks have a fourth door: packages on the openSUSE Build Service (`network:cluster/warewulf-nhc`).

NHC is `noarch`. It's bash scripts plus a few helpers, so there's nothing to compile. "Building" here means generating the install layout and packaging it.

---

## Before you start: the one trap everyone falls into

Every GitHub release page shows **"Source code (zip)"** and **"Source code (tar.gz)"** at the bottom of the assets list. **Do not use those.** GitHub generates them from the Git tree, and they lack the generated `configure` script and friends, so `./configure` won't exist. Grab the `lbnl-nhc-<version>.tar.xz` asset that the NHC team uploaded instead.

> [!WARNING]
> If you see `bash: ./configure: No such file or directory`, you downloaded the GitHub auto-archive. Either grab the real tarball or treat it as a Git checkout (Route C) and run `./autogen.sh` first.

Requirements are refreshingly short: `bash` 4.3 or newer, the usual coreutils, and `make`. Route C additionally needs `autoconf` and `automake`. Upstream commits to supporting the two or three most recent RHEL releases still in vendor support.

---

## Route A: release RPM (RHEL, Rocky, Alma, Oracle)

1. Open the [latest release](https://github.com/mej/nhc/releases/latest) and copy the link of the RPM matching your EL version.
2. Install it:

   ```bash
   # replace the URL with the asset you picked
   dnf install -y https://github.com/mej/nhc/releases/download/<version>/lbnl-nhc-<version>-<release>.el9.noarch.rpm
   rpm -q lbnl-nhc
   nhc -V          # 1.5+: prints version; add more -V for paths and runtime setup
   ```

3. No RPM for your exact EL version? Rebuild the source RPM:

   ```bash
   rpmbuild --rebuild lbnl-nhc-<version>-<release>.src.rpm
   ls ~/rpmbuild/RPMS/noarch/
   ```

> [!NOTE]
> The old LBNL-hosted Yum repo is gone. For a fleet, mirror the RPM into your own repo (Pulp, Satellite, a plain `createrepo` directory) instead of pointing hundreds of nodes at GitHub.

---

## Route B: release tarball (any distro)

```bash
VER=1.5    # check the releases page for the current version
curl -LO https://github.com/mej/nhc/releases/download/${VER}/lbnl-nhc-${VER}.tar.xz
tar xf lbnl-nhc-${VER}.tar.xz
cd lbnl-nhc-${VER}

./configure --prefix=/usr --sysconfdir=/etc --libexecdir=/usr/libexec
make test        # optional, strongly recommended
sudo make install
```

On Debian/Ubuntu you'll often see `--libexecdir=/usr/lib` instead, so helpers land in `/usr/lib/nhc` (Azure's Ubuntu images do this). Either works, as long as you're consistent across the fleet.

Want a `.deb` instead of `make install` sprinkling files around? Wrap the install with your packaging tool of choice (`checkinstall`, `fpm`, or a proper `debian/` directory). Your future self, running `dpkg -L` during an incident, will thank you.

---

## Route C: straight from Git

```bash
git clone https://github.com/mej/nhc.git
cd nhc
git log --oneline -3          # see what you're getting; `git switch dev` for bleeding edge

./autogen.sh                  # generates ./configure (needs autoconf/automake)
./configure --prefix=/usr --sysconfdir=/etc --libexecdir=/usr/libexec
make test
```

Now either install directly, or produce RPMs the way upstream does:

```bash
make dist                     # creates lbnl-nhc-<version>.tar.xz (or .gz)
rpmbuild -ta lbnl-nhc-*.tar.*
ls -lR ~/rpmbuild/RPMS
```

> [!TIP]
> NHC deliberately avoids `nhc.in`-style generated files, so you can run `./nhc` directly from a clone. Handy for testing a fix before packaging it.

---

## Where everything lands

Whichever route you took (with the prefixes above), you get this layout:

| Path | What it is |
|------|-----------|
| `/usr/sbin/nhc` | The driver script. This is what Slurm will run. |
| `/usr/sbin/nhc-genconf` | Scans a node and writes a starter config ([part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md)). |
| `/usr/sbin/nhc-wrapper` | Runs NHC from cron/loops with de-duplicated e-mail alerts. |
| `/etc/nhc/nhc.conf` | The config. The shipped one is a *catalogue of examples*, not a working config. |
| `/etc/nhc/scripts/*.nhc` | Check modules (`common.nhc`, `lbnl_fs.nhc`, `lbnl_hw.nhc`, `lanl_nvgpu.nhc`, ...). Only files ending in `.nhc` are loaded. |
| `/usr/libexec/nhc/node-mark-offline`, `node-mark-online` | Helpers that talk to Slurm/PBS/SGE/LSF. |
| `/etc/sysconfig/nhc` (RHEL) or `/etc/default/nhc` (Debian-ish) | Optional "early" settings sourced before the config. |
| `/var/log/nhc.log` | The run log. A logrotate snippet ships with the package. |
| `/var/run/nhc/` | Detached-mode result files and (1.5+) the per-context PID file. |

Not sure where *your* build put things? On 1.5:

```bash
nhc -V -V -V     # version, runtime setup, and path settings
```

---

## Smoke test

Two tests, thirty seconds:

```bash
# 1. Run ONE check without reading any config, no draining involved
sudo nhc -e 'check_fs_mount_rw -f /' && echo "root fs is rw, NHC works"

# 2. Run the shipped config, verbose, to stdout, never touching the scheduler
sudo nhc -d -v -t 0 -l- MARK_OFFLINE=0
```

The second one will probably *complain* (the stock config is generic). That's fine. Writing a config that fits your nodes is [part 3](/fields/system-administration/node-health-check/writing-nhc-conf.md).

> [!IMPORTANT]
> Notice the shape of that second command: **options first, then `VAR=value` pairs**. NHC reads trailing `VAR=value` arguments as settings, and they must come after every flag.

What does `make test` look like when it's happy? Every module reports `ok N/N` and it finishes with an "All N tests passed" line. Any failure there is worth a GitHub issue, since it means something about your platform breaks NHC's assumptions.

---

## Getting it onto 500 nodes

Installing by hand on one node is a lab exercise. In production:

1. **Bake the package into the node image** (Warewulf, xCAT, Bright/BCM, OpenHPC recipes, or your golden image pipeline). The binary rarely changes.
2. **Manage the config separately** with your config-management tool, because the config changes often. Keep `nhc.conf` and any custom `.nhc` modules in Git.
3. **Pin the version.** Treat an NHC upgrade like any other change: read the release notes (1.5 has a breaking change in `check_file_stat` option letters), test on a few nodes, then roll.

A minimal Ansible sketch:

```yaml
- name: NHC package
  ansible.builtin.dnf:
    name: lbnl-nhc
    state: present

- name: NHC config
  ansible.builtin.template:
    src: nhc.conf.j2
    dest: /etc/nhc/nhc.conf
    owner: root
    mode: "0644"

- name: Site check modules
  ansible.builtin.copy:
    src: "files/nhc/{{ item }}"
    dest: "/etc/nhc/scripts/{{ item }}"
    mode: "0644"
  loop: [acme_gpu.nhc]
```

How to roll the *config* out without draining the whole cluster by accident has its own page: [part 5](/fields/system-administration/node-health-check/rollout-at-scale.md).

> **Takeaway:** use the release tarball or RPM (never GitHub's auto "Source code" archives), run `make test`, put the package in the image and the config in Git.

### References
- [NHC README: Installation and Testing](https://github.com/mej/nhc#installation)
- [NHC releases](https://github.com/mej/nhc/releases)
- [UCL-ARC fork: building RPMs with `make dist` + `rpmbuild -ta`](https://github.com/UCL-ARC/nhc)
