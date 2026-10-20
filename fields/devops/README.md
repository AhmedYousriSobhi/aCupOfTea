---
sidebar_label: DevOps
sidebar_group: DevOps
---

# DevOps: Where Code Meets the Machines That Run It

Somewhere between "it works on my laptop" and "it works for 4,000 users at 3 AM" lives a whole discipline whose job is to make the second sentence true. This is the corner of the repo where we spill the tea on that discipline: clusters, containers, pipelines and the dashboards that tell you which of them is currently on fire.

The focus is practical and HPC-flavoured. Examples lean on GPU clusters, Slurm-style thinking and real lab setups, because that is where most of these notes were born.

---

## The menu

| Section | What you'll find | Best with |
| --- | --- | --- |
| [Kubernetes](/fields/devops/kubernetes/README.md) | Core concepts, a two-node lab you can break on purpose, RBAC, monitoring, and what changes at HPC scale | A strong builder's tea |
| Observability | Prometheus, DCGM Exporter, Grafana, and the difference between "allocated" and "utilized" | *Brewing* |
| CI/CD | Pipelines that fail early and loudly, instead of late and quietly | *Brewing* |

Sections marked *Brewing* are planned and have no pages yet.

---

## Neighbours worth knowing

DevOps overlaps with a few folders that already exist. Those pages stay where they are; this section links to them instead of copying them.

| If you're looking for... | Go to |
| --- | --- |
| Slurm and other batch schedulers | [schedulers](/fields/schedulers/) |
| Linux administration and cluster plumbing | [system-administration](/fields/system-administration/) |
| Containers on HPC (Podman, Apptainer and friends) | [libraries-frameworks-containers](/fields/libraries-frameworks-containers/) |

---

## How the pages are written

- **Short.** One idea per page, finishable before the tea goes cold.
- **Checked against the source.** Claims about how Kubernetes behaves are verified against the official documentation, and each page lists its references at the bottom.
- **Honest about limits.** If something was only read and never run, the page says so.
- **Tested where it says it was.** Lab commands come from a real two-node k3s lab. Anything untested is marked.