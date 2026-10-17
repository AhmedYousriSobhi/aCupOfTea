---
id: broken-pods-rogues-gallery
sidebar_label: Broken Pods, the Rogues' Gallery
summary: "How to recognise CrashLoop, OOMKilled, ImagePull and Pending pods by reading status, events and previous logs."
level: intermediate
type: [concept, guide]
domains: [systems-and-hpc, devops, kubernates]
tags: [kubernetes, hpc, devops, nvidia]
relations:
  prerequisites: [kubernetes-in-five-nouns]
  related: [containers-101]
---

# Broken Pods: A Rogues' Gallery (and the One Command That Catches Them All)

Healthy pods are boring. They run, they get no attention, and nobody writes a blog post about them. The interesting ones are the delinquents: the pod that restarts every few minutes like a bad habit, the one that was killed for eating too much, the one that can't find its own image, and the one waiting for a GPU that doesn't exist.

This page introduces four of them. They come from the [two-node lab](/fields/devops/kubernetes/build-a-two-node-k3s-lab.md) and the [fake GPU trick](/fields/devops/kubernetes/fake-gpus-in-kubernetes.md), where you can create each one on purpose and learn to recognise it on sight.

---

## The one-sentence version

**Every broken pod leaves clues in the same three places: its status, its events, and its previous logs, and you should read them in that order before you touch anything.**

---

## The detective's routine

Whatever the symptom, start here:

```bash
kubectl get pods -A                                 # the status column is clue #1
kubectl describe pod <pod> -n <ns>                  # the Events at the bottom are clue #2
kubectl logs <pod> -n <ns> --previous               # what the last attempt said before dying
kubectl get events -n <ns> --sort-by=.lastTimestamp # the namespace's recent story
```

Read the events **before** you restart anything. Events are short-lived (the API server keeps them for one hour by default, as covered in [Kubernetes in Five Nouns](/fields/devops/kubernetes/kubernetes-in-five-nouns.md)), and a restart can add noise on top of the evidence.

One vocabulary point that trips people up: a pod has a **phase** (`Pending`, `Running`, `Succeeded`, `Failed`), and its containers have **status reasons** (`CrashLoopBackOff`, `ImagePullBackOff`, `OOMKilled`). `CrashLoopBackOff` is a container status reason, not a pod phase, which is why a pod can show it while the pod itself is technically still going.

---

## The gallery

| Rogue | What it does | What you'll see |
| --- | --- | --- |
| `crashloop` | Starts, exits with an error, repeats forever | `CrashLoopBackOff`, climbing restart count |
| `oom` | Uses more memory than its limit allows | `OOMKilled` as the last termination reason |
| `badimage` | Points at an image that can't be pulled | `ErrImagePull`, then `ImagePullBackOff` |
| `gpu-waiting` | Asks for more GPUs than any node has | Stuck in `Pending`, with a scheduling event |

### 1. The crash looper

```bash
kubectl create ns team-b
kubectl -n team-b run crashloop --image=rancher/mirrored-library-busybox:1.36.1 \
  -- sh -c 'echo failing; exit 1'
```

The container prints a line and exits with status 1. By default the pod's restart policy brings it back, so the kubelet restarts it, and it fails again. To keep a broken container from restarting in a frantic loop, the kubelet waits longer after each failure: the delay is exponential (10s, 20s, 40s, and so on) and capped at five minutes. If the container then runs for ten minutes without trouble, the kubelet resets the delay.

That behaviour explains two things people find puzzling:

- A pod in `CrashLoopBackOff` is not hung. It's **between attempts**, and the status shows while the kubelet waits out the delay.
- Once the delay hits its cap, the pod only retries about once every five minutes, so a slow crash loop can look like an intermittent outage instead of a hard failure.

How to investigate:

```bash
kubectl logs crashloop -n team-b --previous   # the failing run's output
kubectl describe pod crashloop -n team-b      # look for "Back-off restarting failed container"
```

`--previous` is the part beginners miss. The current container may have just started and have nothing to say; the interesting output belongs to the one that died.

### 2. The one that ate too much

This one is created by giving a pod a deliberately tiny memory limit and a workload that allocates more than that. When a container exceeds its memory limit, the kernel kills it, and Kubernetes records the reason. Ask for it directly:

```bash
kubectl get pod oom -n team-b \
  -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'
# OOMKilled
```

If the restart policy brings it back, you'll see the same restart-and-back-off pattern as the crash looper, and the distinguishing clue is the `lastState` reason, which is why you ask for it by name. The usual fixes are raising the limit, or fixing the leak. Raising limits without understanding the leak just moves the cliff.

### 3. The one that can't find its image

```bash
kubectl -n team-b run badimage --image=example.invalid/none:1
```

The `.invalid` top-level domain is reserved so that it can never resolve, which makes it a perfect stand-in for "this registry does not exist." The pod first reports `ErrImagePull`, and after failed attempts it settles into `ImagePullBackOff`, another back-off pattern, this time for pulling. In real life the causes are usually a typo in the image name or tag, a private registry without credentials, or a registry the node can't reach. `kubectl describe pod` shows the exact pull error in its events, which tells you which of those it is.

### 4. The one waiting for a GPU

```bash
kubectl -n team-b run gpu-waiting --image=rancher/mirrored-pause:3.6 \
  --overrides='{"spec":{"containers":[{"name":"c","image":"rancher/mirrored-pause:3.6","resources":{"limits":{"nvidia.com/gpu":"8"}}}]}}'
```

The lab's only GPU node advertises four GPUs, so no node can ever host this pod. It stays `Pending`, and the clue is in the events:

```bash
kubectl describe pod gpu-waiting -n team-b
# Warning  FailedScheduling ... Insufficient nvidia.com/gpu
```

A `Pending` pod isn't running, so it isn't consuming anything. It's a request that nobody can grant. That's different from the first three rogues, whose containers actually started and failed. The fix is on the cluster side (more capacity, a smaller request, or waiting for another job to finish), not in the container.

---

## A quick triage table

| Pod status | Container started? | First place to look |
| --- | --- | --- |
| `Pending` | No (not scheduled yet) | `describe` events: scheduling failures |
| `ErrImagePull` / `ImagePullBackOff` | No (image can't be fetched) | `describe` events: the pull error |
| `CrashLoopBackOff` | Yes, and it exits | `logs --previous` and the exit code |
| Restarting with `OOMKilled` | Yes, and it's killed | `lastState.terminated.reason`, then memory limits |
| `Running` but not ready | Yes, but probes fail | `describe` events, then readiness probe config |

---

## Why this matters on HPC clusters

On a batch system you're used to a job that fails once and stays failed. Kubernetes' default instinct is the opposite: keep trying. That's great for web servers and surprising for GPU jobs, where a crash-looping pod that holds GPUs between attempts is a quiet way to waste an expensive resource, and a `Pending` pod can hide a quota or capacity problem for hours. A good monitor treats these four states as first-class signals, which is exactly what the later pages on monitoring build on.

---

## The one-paragraph takeaway

Broken pods are not mysterious; they're just chatty in three specific places. Read the status, read the events, read the previous logs, in that order, and you can usually name the culprit in under a minute: crash looping (look at `--previous`), OOM killed (check `lastState`), image pull failing (read the pull error), or Pending with a scheduling event (the cluster can't grant the request). Don't restart first. The evidence is fragile.

---

## References

- Kubernetes restart back-off behaviour (10s, 20s, 40s, capped at five minutes, reset after ten minutes without trouble): described in [KEP-4603, Tune Crashloop Backoff](https://www.kubernetes.dev/resources/keps/4603/) in the Kubernetes enhancement proposals. The defaults can change in newer releases, so check the current Pod lifecycle documentation for your version.
- [Pods](https://kubernetes.io/docs/concepts/workloads/pods/): controllers and restart behaviour
- [kube-apiserver reference](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/): `--event-ttl`, default one hour
- [Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/): GPUs requested under `limits`

The four fixtures, the lab commands and the triage table are the author's own. The `FailedScheduling` event text and the exact status strings shown are typical `kubectl` output; yours may differ slightly by version, so check what your cluster prints.