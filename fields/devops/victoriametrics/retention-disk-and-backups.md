
# Retention, Full Disks and Backups: Looking After the Data Once It Lands

<!-- related-block -->
<div class="reading-time">11 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [A Single Node You Can Trust: Installing VictoriaMetrics Properly](/fields/devops/victoriametrics/single-node-in-ten-minutes.md)  ·  **See also:** [MetricsQL Surprises and Alerts You Can Test](/fields/devops/victoriametrics/metricsql-and-vmalert.md), [VictoriaMetrics Cheatsheet: Every Step from the Series](/fields/devops/victoriametrics/cheatsheet.md), [vmagent and the Network Blip: Keeping Metrics Through an Outage](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md)

</div>


> **Part 4 of the [VictoriaMetrics series](/fields/devops/victoriametrics/README.md).** [Part 3](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md) got every sample to the database. This page keeps them there: how much disk you really need, what happens when it runs out, and a backup you've actually restored.

- [Healthy, according to the health check](#healthy-according-to-the-health-check)
- [What retention really deletes, and when](#what-retention-really-deletes-and-when)
- [Sizing the disk from a real test](#sizing-the-disk-from-a-real-test)
- [When the disk fills up](#when-the-disk-fills-up)
- [Backups: snapshot, copy, restore](#backups-snapshot-copy-restore)
- [An hourly job you can leave running](#an-hourly-job-you-can-leave-running)
- [Proving the backup](#proving-the-backup)
- [Changing retention safely](#changing-retention-safely)
- [Back to the weekend](#back-to-the-weekend)
- [References](#references)

---

## Healthy, according to the health check

The metrics disk fills up on a Saturday. Your uptime checker polls `/health` every minute, gets `OK`, and stays green all weekend. On Monday the dashboards end at Saturday 03:00. The database was up the whole time. It just wasn't storing anything.

We reproduced that exact situation in the lab. It's the most important thing on this page, and it's in [When the disk fills up](#when-the-disk-fills-up). First, how the disk gets used.

> [!NOTE]
> Lab: VictoriaMetrics **v1.156.0** on a throwaway Ubuntu 24.04.5 sandbox, scraping node_exporter 1.12.1. The backup job ran as the `victoriametrics` user against the layout from [part 2](/fields/devops/victoriametrics/single-node-in-ten-minutes.md), with `127.0.0.1` in place of `10.0.0.5`. systemd wasn't running, so the timer was linted but not started.

---

## What retention really deletes, and when

`-retentionPeriod` takes a number and a unit: `h`, `d`, `w`, `M` (months) or `y`. With no unit it means months. The default is `1M`, which is 31 days, and the minimum is `1d`.

> [!WARNING]
> Lowercase `m` is minutes, and for retention it's refused outright. `-retentionPeriod=3m` exited 2 in the lab: "duration in months must be set with capital `M` suffix, lower case `m` means minutes and not allowed". Good: one character can't quietly turn three months into three minutes.

Data is stored in **monthly partitions** (folders like `2026_11`) made of **parts**. That shapes deletion:

- A whole partition outside retention is deleted **on the first day of the next month**.
- A part outside retention is deleted **eventually**, during a background merge, and only once the part is entirely outside retention.

So the docs' rule is that disk usage peaks at **retention plus one month**. With `-retentionPeriod=1`, January's data is deleted on March 1st. Plan the disk for the peak, not for the setting.

| `-retentionPeriod` | Plan disk for about |
| --- | --- |
| `31d` (the default) | 2 months of data |
| `90d` | 4 months of data |
| `1y` | 13 months of data |

---

## Sizing the disk from a real test

The docs' method: run a test instance on the real workload for **a day**, measure the data directory, and multiply. Ten gigabytes after one day means at least 1 TB for 100 days.

Why a full day and not ten minutes? Our lab shows the trap. After a short run, here's what the database reported about itself:

```bash
curl -s http://127.0.0.1:8431/metrics | grep -E '^vm_data_size_bytes\{type="(storage/small|indexdb/file)"|^vm_rows\{type="storage/small"'
```

```text
vm_data_size_bytes{type="storage/small"} 53867
vm_data_size_bytes{type="indexdb/file"} 79398
vm_rows{type="storage/small"} 39990
```

That's 1.35 bytes per sample for the data, and an index bigger than the data itself. After forcing the background merge that normally happens over time (`/internal/force_merge`), the same 39,990 samples took 27,127 bytes: 0.68 bytes per sample. Halved, just from merging.

A short test over-counts the data, because it hasn't been merged yet, and over-weights the index, because every series is new. A day-long test catches both, plus your daily churn.

Then leave room on top of the peak. The docs recommend:

| Resource | Keep free | Why |
| --- | --- | --- |
| Disk at `-storageDataPath` | At least 20% | Merges need room. Without it, parts pile up and queries slow down |
| RAM | 50% | Less chance of OOM; going past it causes cache evictions and slowdowns |
| CPU | 50% | Headroom for spikes |

Rule of thumb: **disk = (one test day) × (retention days + 31) ÷ 0.8.**

---

## When the disk fills up

When free space at `-storageDataPath` drops below `-storage.minFreeDiskSpaceBytes` (default 100 MB in v1.156.0), the database switches to **read-only mode**: queries still work, new data is refused.

We forced it without filling a disk, by setting the threshold to 100 TB on a disk with 30 GB free:

```bash
victoria-metrics-prod -storageDataPath=./data -httpListenAddr=127.0.0.1:8428 \
  -storage.minFreeDiskSpaceBytes=100TB
```

Writes were refused with HTTP 503, and the mode clears by itself once space is freed ([tested further down](#back-to-the-weekend)):

```text
cannot store metrics: the storage is in read-only mode; check -storage.minFreeDiskSpaceBytes command-line flag value
```

And here's the trap:

```bash
curl -s -w ' http=%{http_code}\n' http://127.0.0.1:8428/health
```

```text
OK http=200
```

**`/health` says OK while every write is being rejected.** It tells you the process is up, not that it's storing anything. The signal is a metric:

```text
vm_storage_is_read_only{path=".../data"} 1
```

Now the second trap. We turned on self-scraping (`-selfScrapeInterval=5s`) on the read-only instance and waited 45 seconds. Querying `vm_storage_is_read_only` on that same instance returned **nothing**. Of course: it's read-only, so it can't store its own metrics either. A database that monitors only itself goes blind in exactly the failure you care about.

> [!IMPORTANT]
> Scrape every VictoriaMetrics from **somewhere else**, a second small instance or a vmagent writing to one, and alert on `vm_storage_is_read_only == 1` there. In the lab, vmalert on a separate monitoring instance fired `VMStorageReadOnly` for the read-only one within two minutes. Part 5 has the rule and its tests.

Data sent through a buffer survives read-only mode. We pointed a vmagent at a read-only instance. In the first run, after 30 seconds it had twenty `503`s, 46 KB queued and nothing dropped. In a second, timed run of 63 seconds, it delivered every sample for the read-only window once the threshold was lifted: 12 of 12. Targets scraped by the read-only node itself have no buffer, so those samples are simply lost. One more reason for the vmagent in [part 3](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md).

---

## Backups: snapshot, copy, restore

A **snapshot** is an instant, read-only view of the data directory, made with hard links, so it's free to create. **vmbackup** asks the database for a snapshot, copies it to the destination (`s3://`, `gs://`, `azblob://` or `fs://`), and deletes the snapshot. If the destination already holds a backup, only the changed files are uploaded. **vmrestore** copies a backup back into a stopped database's data directory.

Every failure path we tried was refused cleanly:

| What we tried | What happened |
| --- | --- |
| Backup without the snapshot key | `401` from `/snapshot/create`, exit 255 |
| Backup into the data directory itself | Refused: `-dst ... can not point to the directory with VictoriaMetrics data`, exit 255 |
| Restore while the database was running on that directory | Panic: `cannot acquire lock on file ".../flock.lock"`, exit 2, nothing touched |
| Restore into a fresh directory, then start on it | 645 series, same as the source |
| Second backup to the same destination | Incremental: 97 bytes uploaded |

Two traps worth knowing before you automate it:

**The key ends up in the log.** You can keep the key out of `ps` with `%{ENV_VAR}` in the flag value: VictoriaMetrics expands it itself, and in the lab a running process's command line showed the literal `%{K}`, not the key. But vmbackup then logs the expanded URL, key included. Both on success:

```text
info ... Snapshot create url http://127.0.0.1:8429/snapshot/create?authKey=k3y
```

and on failure. That's why [part 2](/fields/devops/victoriametrics/single-node-in-ten-minutes.md) uses a separate snapshot key that can't delete anything.

**An interrupted backup leaves a snapshot behind.** We throttled a backup with `-maxBytesPerSecond=2000` and killed it after 3 seconds. `vm_snapshots` went from 0 to 1, and stayed at 1 after a successful rerun. Old snapshots hold on to parts that merges would otherwise free, so they slowly eat disk. Since **v1.122.0**, `-snapshotsMaxAge` defaults to `3d`, and in the lab a 60-second setting deleted the orphan on schedule. On older versions the default is to keep snapshots forever, so set it yourself, longer than your slowest backup.

---

## An hourly job you can leave running

This follows the docs' "smart backups" pattern: an hourly incremental into `latest/`, and once a day a server-side copy of `latest/` into a dated folder. The docs say the two shouldn't overlap, so one script does both, in order. `set -e` means the daily copy only happens after a successful hourly run.

1. Install vmbackup and vmrestore from the `vmutils` tarball (verify it like in part 2), and make the backup folder:

```bash
install -m 0755 vmbackup-prod vmrestore-prod /usr/local/bin/
install -d -o victoriametrics -g victoriametrics -m 0750 /backup/victoriametrics
```

2. The script:

```bash
cat > /usr/local/sbin/vm-backup <<'EOF'
#!/usr/bin/env bash
# Hourly: incremental backup into latest/. Once a day: server-side copy of latest/ into YYYYMMDD/.
# Run as the victoriametrics user. Exits non-zero on any failure.
set -euo pipefail

VM_URL=http://10.0.0.5:8428
DATA=/var/lib/victoriametrics
DST=/backup/victoriametrics
DAILY_HOUR=00
KEEP_DAYS=14

VM_SNAPSHOT_KEY=$(cat /etc/victoriametrics/snapshot.key)
export VM_SNAPSHOT_KEY

/usr/local/bin/vmbackup-prod -loggerLevel=ERROR \
  -storageDataPath="$DATA" \
  -snapshot.createURL="$VM_URL/snapshot/create?authKey=%{VM_SNAPSHOT_KEY}" \
  -dst="fs://$DST/latest"

if [ "$(date +%H)" = "$DAILY_HOUR" ]; then
  /usr/local/bin/vmbackup-prod -loggerLevel=ERROR \
    -origin="fs://$DST/latest" -dst="fs://$DST/$(date +%Y%m%d)"
  cutoff=$(date -d "$KEEP_DAYS days ago" +%Y%m%d)
  for d in "$DST"/[0-9]*; do
    name=$(basename "$d")
    if [[ $name =~ ^[0-9]{8}$ ]] && [ "$name" -lt "$cutoff" ]; then
      rm -rf -- "$d"
    fi
  done
fi
echo "vm-backup: ok"
EOF
chmod 0755 /usr/local/sbin/vm-backup
```

The pruning loop uses `if`, not `[[ ]] && [ ] && rm`, on purpose: with `set -e`, a `&&` chain that's false on the last folder makes the whole script exit non-zero after a perfectly good backup.

3. Run it once by hand and check:

```bash
runuser -u victoriametrics -- /usr/local/sbin/vm-backup; echo "exit=$?"
```

```text
vm-backup: ok
exit=0
```

In the lab we also ran it with `DAILY_HOUR` set to the current hour. It made the dated copy, deleted a planted `20200101` folder, and kept a 3-day-old one and a folder called `notes`. With a wrong key, and with the database stopped, it exited 255.

4. The timer:

```bash
cat > /etc/systemd/system/vm-backup.service <<'EOF'
[Unit]
Description=VictoriaMetrics backup (hourly incremental, daily copy)
After=network-online.target

[Service]
Type=oneshot
User=victoriametrics
Group=victoriametrics
ExecStart=/usr/local/sbin/vm-backup
EOF

cat > /etc/systemd/system/vm-backup.timer <<'EOF'
[Unit]
Description=Run vm-backup every hour

[Timer]
OnCalendar=*-*-* *:05:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now vm-backup.timer
```

Success: `systemctl list-timers vm-backup.timer` shows the next run at five past the hour. Both units passed the output-based lint from part 2, but weren't started in the lab.

> [!CAUTION]
> `fs://` on a local disk protects you from mistakes, not from losing the machine. Point `DST` at an NFS mount on another host, or switch to `s3://` with `-credsFilePath`, before you call this a backup. vmbackup is the same tool either way.

---

## Proving the backup

**A backup you haven't restored is a rumour.** Once a month, restore the latest dated backup somewhere harmless and compare it to the live database:

```bash
vmrestore-prod -src=fs:///backup/victoriametrics/$(date +%Y%m%d) \
  -storageDataPath=/srv/restore-test -loggerLevel=ERROR
victoria-metrics-prod -storageDataPath=/srv/restore-test -httpListenAddr=127.0.0.1:8435 &
curl -s http://127.0.0.1:8435/api/v1/query \
  --data-urlencode 'query=count(count_over_time({job="node"}[2h]))'
```

In the lab, the restored copy and the live database both answered `645`. Remember the restore target must not be in use: vmrestore makes the folder match the backup exactly, deleting anything extra, like `rsync --delete`. That's what the lock file protects you from.

---

## Changing retention safely

Raising `-retentionPeriod` is safe. Lowering it deletes data, eventually, with no undo. Treat it like any risky change:

1. **Dry run:** work out what goes. Everything older than the new retention, at the next merge or month boundary.
2. **Backup:** run `vm-backup` by hand and confirm `exit=0`.
3. **Canary:** if you run two identical nodes behind vmagent (part 3), change one first and watch `vm_data_size_bytes` for a day.
4. **Enforce:** change the other.
5. **Rollback:** there's no un-deleting. Rollback means `vmrestore` from step 2 into a stopped node.

---

## Back to the weekend

The same Saturday, with this page in place.

The disk was sized for retention plus a month, with 20% to spare, so on its own it doesn't fill. Say it fills anyway, because someone parked a core dump on the same filesystem. At 03:00 the database switches to read-only. `/health` still says `OK`, but the monitoring instance is scraping it from outside, sees `vm_storage_is_read_only 1`, and `VMStorageReadOnly` pages after a minute. In the lab it fired in under two.

Nothing sent through vmagent is lost while that page waits for a human: the queue absorbs the `503`s, just as it delivered 12 of 12 samples in the lab.

The on-call admin deletes the core dump. That's it. No restart. The database re-checks free space about once a second and switches itself back. We tested that on a real full disk: a 300 MB tmpfs with a 150 MB threshold. Writing a 200 MB file turned writes from `204` into `503`; deleting it turned them back into `204` within seconds, and the log said so both ways:

```text
warn ... switching the storage at /mnt/vmtiny/data to read-only mode, since it has less than -storage.minFreeDiskSpaceBytes=150000000 of free space ...
warn ... switching the storage at /mnt/vmtiny/data to read-write mode, since it has more than -storage.minFreeDiskSpaceBytes=150000000 of free space ...
```

vmagent drains its queue, and Monday's dashboards have Saturday in them. If it had been worse and the disk had died, the hourly backup caps the loss at the hour since the last run, and you already know the restore works because you tested it last month.

**Takeaway:** plan disk for retention plus a month, alert on `vm_storage_is_read_only` from outside the database, and keep a backup job whose restore you've actually tested.

**Next:** [Part 5, MetricsQL Surprises and Alerts You Can Test](/fields/devops/victoriametrics/metricsql-and-vmalert.md), writes the alerts this page keeps promising.

---

## References

- [VictoriaMetrics single-node docs](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/): retention, storage (partitions, parts, merges, 20% free disk), capacity planning, snapshots and snapshot troubleshooting, environment variables and `%{ENV_VAR}`, self-scraping.
- [Common command-line flags](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/#list-of-command-line-flags): `-retentionPeriod`, `-storage.minFreeDiskSpaceBytes` (default 100000000), `-snapshotsMaxAge`, `-selfScrapeInterval`.
- [vmbackup](https://docs.victoriametrics.com/victoriametrics/vmbackup/): storage types, incremental and smart backups, server-side copy, how it works, troubleshooting.
- [vmrestore](https://docs.victoriametrics.com/victoriametrics/vmrestore/): the database must be stopped; restore syncs like `rsync --delete`.
- [VictoriaMetrics changelog 2025](https://docs.victoriametrics.com/victoriametrics/changelog/changelog_2025/): v1.122.0 changed the `-snapshotsMaxAge` default to `3d`.
- [systemd.timer(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html): `OnCalendar` and `Persistent`.
