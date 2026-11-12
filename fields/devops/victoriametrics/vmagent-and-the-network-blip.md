---
id: vm-vmagent-buffering
title: "vmagent and the Network Blip: Keeping Metrics Through an Outage"
sidebar_label: "3. vmagent and the network blip"
order: 3
summary: How vmagent buffers metrics on disk while storage is down, the URL edit that silently deletes that buffer, the v1.156.0 flag that prevents it, and how to size the queue.
level: intermediate
type: [concept, guide]
domains: [devops, systems-and-hpc]
tags: [victoriametrics, monitoring]
relations:
  prerequisites: [vm-single-node]
---

# vmagent and the Network Blip: Keeping Metrics Through an Outage

> **Part 3 of the [VictoriaMetrics series](/fields/devops/victoriametrics/README.md).** [Part 2](/fields/devops/victoriametrics/single-node-in-ten-minutes.md) gave you a single node that scrapes its own targets. This page moves scraping to a vmagent and proves, on a lab, that it keeps every sample through a storage outage, and the one edit that throws them away.

- [The switch upgrade](#the-switch-upgrade)
- [Collect at the edge, store in the middle](#collect-at-the-edge-store-in-the-middle)
- [Run it](#run-it)
- [The outage test](#the-outage-test)
- [The trap: tidy up a URL, lose the buffer](#the-trap-tidy-up-a-url-lose-the-buffer)
- [The fix: pin the queue path](#the-fix-pin-the-queue-path)
- [How big should the buffer be?](#how-big-should-the-buffer-be)
- [What vmagent is not for](#what-vmagent-is-not-for)
- [Back to the switch upgrade](#back-to-the-switch-upgrade)
- [References](#references)

---

## The switch upgrade

The network team upgrades the core switch on Sunday morning. Forty minutes of maintenance, announced weeks ago. The compute nodes keep running jobs. The monitoring server, in another rack, can't be reached.

On Monday someone asks why a training run slowed down on Sunday. The dashboard has a forty-minute hole exactly where the answer should be. The exporters were fine the whole time. Nobody was writing down what they said.

You want something next to the exporters that writes it down and hands it over when the network comes back. That's **vmagent**.

---

## Collect at the edge, store in the middle

**vmagent** scrapes targets (same `scrape_configs` as Prometheus) and sends the samples to one or more `-remoteWrite.url` destinations. When a destination can't take data, vmagent writes it to a **persistent queue** on local disk and keeps retrying. When the destination comes back, it sends the backlog.

Four facts from the docs shape everything below:

| Fact | Consequence |
| --- | --- |
| The queue lives under `-remoteWrite.tmpDataPath` (default `vmagent-remotewrite-data`) | It's local disk on the vmagent host. Put it somewhere with room |
| Its size per URL is capped by `-remoteWrite.maxDiskUsagePerURL`, **default 0 = unlimited** | A long outage can fill that disk unless you set a cap |
| When the cap is reached, vmagent **drops the oldest data** to make room | You lose the start of an outage, never the end |
| The backlog is sent oldest-first (FIFO) | After a long outage, fresh data shows up late until the backlog drains |

Where to run it: one vmagent per rack, per site, or on the login nodes. Anywhere that stays reachable from the exporters when the link to storage doesn't.

---

## Run it

> [!NOTE]
> Everything with numbers below was run with vmagent and VictoriaMetrics **v1.156.0** on a throwaway Ubuntu 24.04.5 sandbox, scraping a real node_exporter 1.12.1 every 5 seconds. The 5-second interval is only there to make a one-minute outage produce enough samples to count.

The vmagent binary is in the `vmutils` tarball from the same release, verified the same way as in part 2. A minimal run:

```bash
vmagent-prod \
  -promscrape.config=/etc/vmagent/scrape.yml \
  -remoteWrite.url=http://10.0.0.5:8428/api/v1/write \
  -remoteWrite.tmpDataPath=/var/lib/vmagent \
  -remoteWrite.queuePath=/var/lib/vmagent/queue-central \
  -remoteWrite.maxDiskUsagePerURL=4GiB \
  -httpListenAddr=10.0.1.2:8429
```

Hold that `-remoteWrite.queuePath` line. The rest of the page is about why it's there.

---

## The outage test

We ran vmagent against a central VictoriaMetrics, waited 20 seconds, killed the central database, waited a minute, and looked at vmagent's own metrics:

```bash
curl -s http://127.0.0.1:8430/metrics | grep -E '^vmagent_remotewrite_pending_data_bytes'
```

```text
vmagent_remotewrite_pending_data_bytes{path=".../vmagent-q/persistent-queue/1_9CE28D37044E5A42", url="1:secret-url"} 154767
```

About 150 KB waiting, and the log said what it was doing:

```text
warn ... couldn't send a block with size 8791 bytes to "1:secret-url": ... connection refused; re-sending the block in 1s.
```

(`1:secret-url` is vmagent hiding the URL in its own metrics and logs. That's on purpose.)

Then we started the central database again and counted samples in the outage window. The outage lasted 64 seconds; at one sample every 5 seconds that's about 13:

```bash
curl -s http://127.0.0.1:8429/api/v1/query \
  --data-urlencode 'query=count_over_time(up{job="node"}[64s])' \
  --data-urlencode "time=$OUTAGE_END"
```

```text
"value":[1794393604,"13"]
```

Thirteen. No gap. Pending bytes went back to `0`. That's the behaviour you're paying for.

---

## The trap: tidy up a URL, lose the buffer

Same setup, second outage. This time, while the central database is down and 108 KB are queued, someone "tidies" the config: `http://127.0.0.1:8429/...` becomes `http://localhost:8429/...`. Same server. They restart vmagent. Here's what it logged on start:

```text
info ... opened fast queue at ".../persistent-queue/1_3F185370F349A8A0" ... it contains 0 pending bytes
info ... removing dangling queue "1_9CE28D37044E5A42"
info ... removed 1 dangling queues from ".../vmagent-q", active queues: 1
```

At `info` level, not `warn`. When the database came back, the outage window had **1 sample where 10 were expected.**

Why: by default the queue directory's name is built from the URL's position in the flag list plus a hash of the URL itself. Change the host spelling, reorder two `-remoteWrite.url` flags, or add one in front, and the name changes. On the next start, the old directory has no matching URL, so vmagent calls it dangling and deletes it. The docs describe this exactly; it's easy to miss until it costs you a weekend's data.

> [!CAUTION]
> Never edit, reorder or insert `-remoteWrite.url` flags on a vmagent that has a backlog, unless each URL has a pinned `-remoteWrite.queuePath`. Check first: `vmagent_remotewrite_pending_data_bytes` should be `0`.

Query parameters and fragments are left out of the hash, so `?extra_label=...` edits don't trigger this. Host, port and path changes do.

---

## The fix: pin the queue path

v1.156.0 added `-remoteWrite.queuePath`: one per `-remoteWrite.url`, in the same order, naming the queue directory yourself. We repeated the whole trap with it set:

```bash
vmagent-prod ... \
  -remoteWrite.url=http://127.0.0.1:8429/api/v1/write \
  -remoteWrite.queuePath=/root/vmlab/t2/q-central
# outage, 108 KB queued, then restart with the "tidied" URL:
vmagent-prod ... \
  -remoteWrite.url=http://localhost:8429/api/v1/write \
  -remoteWrite.queuePath=/root/vmlab/t2/q-central
```

```text
info ... opened fast queue at "/root/vmlab/t2/q-central" ... it contains 139320 pending bytes
```

No dangling queue, and the outage window had **10 of about 10** samples once the database returned.

Rules for the flag, from the docs:

- Every `-remoteWrite.queuePath` must be a directory used by one URL only. vmagent **deletes the contents** of a directory that doesn't hold a valid queue, so never point it at something else.
- vmagent doesn't remember which URL a directory belonged to. Point a directory at a different URL and its backlog goes to the new destination.
- Directories you stop using aren't cleaned up. Remove them yourself.
- Upgrading an existing vmagent? Pass the current auto-named directory as the path (`-remoteWrite.queuePath=<tmpDataPath>/persistent-queue/1_9CE28D37044E5A42`) and the backlog carries over.

On versions before v1.156.0 the flag doesn't exist. The only protection there is `-remoteWrite.keepDanglingQueues`, which keeps orphaned directories on disk instead of deleting them, but doesn't send their contents anywhere.

**Recommendation:** on v1.156.0 and later, always set `-remoteWrite.queuePath`. On older versions, set `-remoteWrite.keepDanglingQueues` and drain the queue before you touch a URL.

---

## How big should the buffer be?

Pick how long an outage you want to survive, then measure what vmagent actually sends. The docs give the query:

```text
sum(rate(vmagent_remotewrite_bytes_sent_total[1h])) by (instance, url) * 6h / 1Gi
```

That's the gigabytes needed to hold 6 hours. Use your own number of hours. Then set `-remoteWrite.maxDiskUsagePerURL` to that, rounded up to a multiple of 500 MB because the queue is stored in roughly 500 MB chunks. The docs' floor is 500 MiB per URL.

| Choice | What happens in a long outage |
| --- | --- |
| No cap (the default) | Nothing is dropped until the disk fills. Then whatever else lives on that disk suffers too |
| A cap | The oldest data is dropped once the cap is reached. You keep the most recent hours |
| `-remoteWrite.disableOnDiskQueue` | Nothing is buffered. Scraped samples are dropped while storage can't keep up |

Rule of thumb: **cap it, and size the cap to your longest planned maintenance plus a margin.** Put the queue on its own filesystem if you can.

> [!TIP]
> After a long outage, fresh samples wait behind the backlog. If dashboards need "now" more than they need order, `-remoteWrite.inmemoryQueues` (since v1.146.0) adds workers that send recent data while the backlog drains. The catch: samples can arrive out of order, so don't use it with storage that rejects that. We didn't test this flag.

Then watch it. Part 5 adds an alert on `vmagent_remotewrite_pending_data_bytes` that doesn't fire for every short blip.

---

## What vmagent is not for

- **Long-term storage.** The queue is a waiting room, not a database. You can't query it.
- **High availability by itself.** One vmagent is one point of failure for its targets. The docs' HA pattern is two identically configured vmagents writing to deduplicating storage, which is a bigger topic than this page.
- **Fixing a storage server that's too small.** If the central database can't keep up all the time, the queue just grows until it hits the cap. Fix the server.

---

## Back to the switch upgrade

Run that Sunday again, with a vmagent in each rack and this page's flags.

The core switch goes down. The exporters keep answering their rack's vmagent, which keeps scraping and writes everything to its queue on local disk. Halfway through, a colleague notices the remote-write URL still says the old hostname, "fixes" it and restarts vmagent. The queue path is pinned, so the backlog stays put, just as the lab's 139 KB did. The switch comes back, vmagent sends the backlog oldest first, and the newest minutes show up a little late. On Monday the dashboard has no hole. Whoever asks about the slow training run gets an answer.

Our lab outages lasted about a minute. Forty minutes is a sizing question, not something we ran, so do these three checks before the maintenance window instead of after:

| Before the window | How |
| --- | --- |
| The queue cap covers the outage plus a margin | Run the `vmagent_remotewrite_bytes_sent_total` query from above with your window instead of `6h`, and compare with `-remoteWrite.maxDiskUsagePerURL` |
| Every URL has its own pinned queue | One `-remoteWrite.queuePath` per `-remoteWrite.url` |
| Nobody is mid-backlog when config changes | `vmagent_remotewrite_pending_data_bytes` is `0` before anyone restarts vmagent |

If the queue still isn't draining 15 minutes after the switch is back, the `VMAgentQueueBacklog` alert in [part 5](/fields/devops/victoriametrics/metricsql-and-vmalert.md) tells you, instead of a Monday question.

**Takeaway:** vmagent turns a storage outage into a delay instead of a gap, as long as you cap its queue and pin each queue's path so a URL edit can't delete it.

**Next:** [Part 4, Retention, Full Disks and Backups](/fields/devops/victoriametrics/retention-disk-and-backups.md), looks after the data once it arrives.

---

## References

- [vmagent docs](https://docs.victoriametrics.com/victoriametrics/vmagent/): features, on-disk persistence, manual persistence paths (`-remoteWrite.queuePath`), processing order and `-remoteWrite.inmemoryQueues`, disabling on-disk persistence, calculating disk space for the queue.
- [vmagent command-line flags](https://docs.victoriametrics.com/victoriametrics/vmagent/#advanced-usage): `-remoteWrite.tmpDataPath`, `-remoteWrite.maxDiskUsagePerURL`, `-remoteWrite.keepDanglingQueues`, `-remoteWrite.disableOnDiskQueue`.
- [VictoriaMetrics changelog 2026](https://docs.victoriametrics.com/victoriametrics/changelog/changelog_2026/): v1.156.0 adds `-remoteWrite.queuePath`.
- [High availability for writes](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/#high-availability-for-writes): replicating through vmagent, with deduplication on the storage side.
- [Part 2, A Single Node You Can Trust](/fields/devops/victoriametrics/single-node-in-ten-minutes.md): verifying release tarballs.
