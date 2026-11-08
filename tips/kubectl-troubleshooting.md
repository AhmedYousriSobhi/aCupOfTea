---
id: kubectl-troubleshooting
title: "kubectl Troubleshooting Cheat Sheet: Five Questions, in Order"
summary: "A kubectl cheat sheet for a pod or Job that won't work: where is it, what does it say, what did the cluster say, why did it die, and how to look inside. Commands from the Kubernetes reference."
level: intermediate
type: reference
domains: [devops, systems-and-hpc]
tags: [kubernetes]
relations:
  prerequisites: [kubernetes-in-five-nouns]
  related: [broken-pods-rogues-gallery, kubernetes-at-hpc-scale, oomkilled-with-memory-to-spare]
sidebar_label: kubectl troubleshooting
---

# kubectl Troubleshooting Cheat Sheet: Five Questions, in Order

> **A companion to the [Kubernetes series](/fields/devops/kubernetes/README.md).** It's 6 PM, a pod is wrong, and you remember half of a command. This page is the shelf: five questions, asked in the same order every time, with the command for each.

- [The ritual](#the-ritual)
- [1. Where is it?](#1-where-is-it)
- [2. What does it say?](#2-what-does-it-say)
- [3. What did the cluster say?](#3-what-did-the-cluster-say)
- [4. Why did it die?](#4-why-did-it-die)
- [5. How do I look inside?](#5-how-do-i-look-inside)
- [The Job that lost index 417](#the-job-that-lost-index-417)
- [References](#references)

---

## The ritual

Think of a nurse doing rounds. She doesn't start with surgery. She checks the same five things, in the same order, on every patient, and most of the time the answer is on the second one.

Do the same with a pod. Where is it, what does it say, what did the cluster say about it, why did it die, and only then, how do I look inside. The order matters because each step is cheaper than the next, and the first three fix most tickets. [Part 4](/fields/devops/kubernetes/broken-pods-rogues-gallery.md) is the long version of this ritual with the gallery of failures. This page is the short one.

> [!NOTE]
> Every command here comes from the Kubernetes reference pages read on 8 November 2026. I didn't run this sheet on a cluster. Replace `POD`, `NS` and `JOB` with your own names.

---

## 1. Where is it?

```bash
kubectl get pods -n NS -o wide            # status, restarts, and which node it landed on
kubectl get pods -A                       # every namespace, when you forgot which one
kubectl get pods -l app=web --show-labels # filter by label, and show the labels
```

`-o wide` adds the node name. A pod that is `Pending` has no node yet, and a pod on the wrong node tells you to look at taints and selectors ([part 7](/fields/devops/kubernetes/isolating-gpu-workloads.md)).

The docs give the first split: a pod stuck in `Pending` "can not be scheduled onto a node", usually because of insufficient resources. A pod stuck in `Waiting` was scheduled but "can't run on that machine", most often because the image can't be pulled.

---

## 2. What does it say?

```bash
kubectl logs POD -n NS                    # the container's output so far
kubectl logs POD -c CONTAINER             # pick one container in a multi-container pod
kubectl logs -p POD                       # the PREVIOUS instance, after a restart
kubectl logs POD --tail=20 --since=1h     # the recent part only
kubectl logs -l app=web --all-containers  # every pod matching a label
kubectl logs job/JOB                      # a Job's first container
kubectl logs -f POD --timestamps          # follow it live, with times
```

The one people forget is `-p`. A pod in `CrashLoopBackOff` keeps restarting, so plain `kubectl logs` shows the new, empty instance. The docs describe `--previous` as printing "the logs for the previous instance of the container in a pod if it exists."

Two limits from the docs: with a selector, `--tail` defaults to 10 lines, and `--max-log-requests` defaults to 5 pods followed at once.

---

## 3. What did the cluster say?

```bash
kubectl describe pod POD -n NS            # state, restart count, and the Events at the bottom
kubectl events -n NS --for pod/POD        # just that pod's events
kubectl events -n NS --types=Warning      # only the bad news
kubectl events -A --watch                 # watch events arrive
```

`describe` prints "a detailed description of the selected resources, including related resources such as events". Read the **Events** section at the bottom first: the scheduler writes its reason there, such as `Insufficient nvidia.com/gpu`.

> [!TIP]
> For several pods or a prefix match, `describe` doesn't show events unless you ask: `--show-events` defaults to true only for a single object. Name the pod.

---

## 4. Why did it die?

Logs show what the program said. The pod status shows what Kubernetes saw: the exit code and the reason.

```bash
kubectl get pod POD -o yaml               # look at status.containerStatuses[].lastState.terminated
kubectl get pod POD -o go-template='{{range .status.containerStatuses}}{{.name}}: {{.lastState.terminated.message}}{{"\n"}}{{end}}'
```

Look for `lastState.terminated`: it carries `exitCode`, `reason` and `message`. `OOMKilled` there means the memory limit, and [part 10](/fields/devops/kubernetes/oomkilled-with-memory-to-spare.md) explains why it can happen with RAM to spare.

Your program can leave a note too. The docs say Kubernetes reads a termination message from `/dev/termination-log` by default. If the file is empty and the container failed, setting `terminationMessagePolicy: FallbackToLogsOnError` uses the last chunk of the log instead, limited to 2048 bytes or 80 lines. You can't change `terminationMessagePath` after the pod has started.

| What you see | Where to look |
| --- | --- |
| `Pending` | `describe`, Events: the scheduler's reason |
| `ImagePullBackOff` | `describe`: the image name, the registry, the pull secret |
| `CrashLoopBackOff` | `logs -p`, then `lastState.terminated` |
| `OOMKilled` | `lastState.terminated.reason`, then the memory limit |
| `Completed` but wrong | `logs`: the exit code was 0, so look at the program |

---

## 5. How do I look inside?

Only now. If the pod is up and its image has no shell, `kubectl debug` adds one:

```bash
kubectl debug POD -it --image=busybox                          # an ephemeral debug container in the pod
kubectl debug POD -it --image=busybox --copy-to=my-debugger    # a copy of the pod, so the original is untouched
kubectl debug node/NODE -it --image=busybox                    # a pod on the node, host filesystem at /host
```

The docs describe the first form as adding "an ephemeral container to an already running pod, for example to add debugging utilities without restarting the pod." For a node, "the host's filesystem will be mounted at /host".

My recommendation: prefer `--copy-to` on anything that matters. A debug session in the real pod can disturb the very problem you came to see, and a copy can be thrown away.

> [!WARNING]
> `kubectl debug node/...` runs in the node's host namespaces. Treat it like root on that machine, and check who is allowed to do it ([part 13](/fields/devops/kubernetes/rbac-and-the-limited-viewer.md)).

---

## The Job that lost index 417

[Page 15](/fields/devops/kubernetes/kubernetes-at-hpc-scale.md) ended on a challenge: index 417 of an Indexed Job failed twice. Here is the same ritual, applied to it.

```bash
kubectl get job JOB -o jsonpath='{.status.failedIndexes}'   # which indexes failed
kubectl get pods -l batch.kubernetes.io/job-completion-index=417   # that index's pod, if it still exists
kubectl logs -p -l batch.kubernetes.io/job-completion-index=417    # what it said, if the pod is still there
```

The Job docs say indexes that exceed the per-index backoff limit go into `.status.failedIndexes`, and that the completion index is also a pod label (v1.28 and later). The selector above would match pods from every Job in the namespace that has index 417. In a shared namespace, add the Job's own label to the selector.

If the pod is already gone, as `ttlSecondsAfterFinished` will make it, you have three places left:

```bash
kubectl describe job JOB            # the Job's own events: why pods failed or were replaced
kubectl events --for job/JOB        # the same, as a list
kubectl get job JOB -o yaml         # conditions and counters in status
```

That's all the cluster will tell you. The logs of a deleted pod are gone with it, so a site that expects to debug after the fact needs logs shipped off the cluster before the TTL fires. That is a recommendation, not a Kubernetes rule.

**Takeaway:** ask the same five questions in the same order, and reach for `logs -p` and the Events section before anything else.

---

## References

- [Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/): `describe`, Pending and Waiting pods.
- [kubectl logs](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/): `--previous`, selectors, `--tail`, `--since`, `--max-log-requests`.
- [kubectl events](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_events/): `--for`, `--types`, `--watch`.
- [kubectl describe](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_describe/): events and `--show-events`.
- [kubectl get](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_get/): `-o wide`, selectors, output formats.
- [Determine the reason for Pod failure](https://kubernetes.io/docs/tasks/debug/debug-application/determine-reason-pod-failure/): `lastState.terminated`, termination messages, `FallbackToLogsOnError`.
- [kubectl debug](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/): ephemeral containers, `--copy-to`, node debugging.
- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/): `failedIndexes`, the completion index label, `ttlSecondsAfterFinished`.
