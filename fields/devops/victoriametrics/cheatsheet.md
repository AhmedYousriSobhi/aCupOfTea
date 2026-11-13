
# VictoriaMetrics Cheatsheet: Every Step from the Series

<!-- related-block -->
<div class="reading-time">6 min read</div>
<!-- related-block -->
<div class="related-strip">

**See also:** [A Single Node You Can Trust: Installing VictoriaMetrics Properly](/fields/devops/victoriametrics/single-node-in-ten-minutes.md), [MetricsQL Surprises and Alerts You Can Test](/fields/devops/victoriametrics/metricsql-and-vmalert.md), [Retention, Full Disks and Backups: Looking After the Data Once It Lands](/fields/devops/victoriametrics/retention-disk-and-backups.md), [vmagent and the Network Blip: Keeping Metrics Through an Outage](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md)

</div>


> **Part 6 of [VictoriaMetrics](/fields/devops/victoriametrics/README.md)** The series as one list of commands, in the order you'd run them on a new host. Each step links to the page that explains it, shows its output, and shows how it fails.

- [VictoriaMetrics Cheatsheet: Every Step from the Series](#victoriametrics-cheatsheet-every-step-from-the-series)
  - [Before you start](#before-you-start)
  - [1. Download and verify](#1-download-and-verify)
  - [2. User, directories, keys](#2-user-directories-keys)
  - [3. Scrape config](#3-scrape-config)
  - [4. The service](#4-the-service)
  - [5. Reload safely](#5-reload-safely)
  - [6. vmagent at the edge](#6-vmagent-at-the-edge)
  - [7. Retention and disk](#7-retention-and-disk)
  - [8. Backups](#8-backups)
  - [9. Prove the backup](#9-prove-the-backup)
  - [10. Alerts with tests](#10-alerts-with-tests)
  - [11. Run vmalert](#11-run-vmalert)
  - [Quick reference](#quick-reference)
  - [References](#references)

---

## Before you start

> [!NOTE]
> Every command here appears on one of the series pages, where it was run on a throwaway Ubuntu 24.04.5 sandbox with VictoriaMetrics **v1.156.0**. That sandbox had no running systemd: the unit files were linted but `systemctl start` wasn't run, as each page says. This sheet collects the commands; it wasn't re-run from top to bottom as one script.

Replace `10.0.0.5` (the database) and `10.0.0.6` (a separate monitoring instance) with your addresses.

---

## 1. Download and verify

[Part 2, step 1](/fields/devops/victoriametrics/single-node-in-ten-minutes.md#step-1-download-and-verify).

```bash
VM_VERSION=v1.156.0
REL=https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VM_VERSION}
cd /tmp
for t in victoria-metrics vmutils; do
  curl -fsSLO ${REL}/${t}-linux-amd64-${VM_VERSION}.tar.gz
  curl -fsSLO ${REL}/${t}-linux-amd64-${VM_VERSION}_checksums.txt
  grep "${t}-linux-amd64-${VM_VERSION}.tar.gz" ${t}-linux-amd64-${VM_VERSION}_checksums.txt | sha256sum --check
  tar -xzf ${t}-linux-amd64-${VM_VERSION}.tar.gz
done
install -m 0755 victoria-metrics-prod vmagent-prod vmalert-prod vmalert-tool-prod vmbackup-prod vmrestore-prod /usr/local/bin/
victoria-metrics-prod --version
```

Expected: `...tar.gz: OK` for each tarball (a tampered one prints `FAILED` and exits 1), then `victoria-metrics-...-tags-v1.156.0-...`.

---

## 2. User, directories, keys

[Part 2, steps 2 and 4](/fields/devops/victoriametrics/single-node-in-ten-minutes.md#step-2-a-user-and-two-directories).

```bash
useradd --system --no-create-home --shell /usr/sbin/nologin victoriametrics
install -d -o victoriametrics -g victoriametrics -m 0750 /var/lib/victoriametrics
install -d -m 0755 /etc/victoriametrics
for k in delete snapshot; do
  openssl rand -hex 24 | install -m 0640 -g victoriametrics /dev/stdin /etc/victoriametrics/$k.key
done
ls -l /etc/victoriametrics/
```

Two keys on purpose: vmbackup logs the snapshot key, so it must not be able to delete anything. Put `/var/lib/victoriametrics` on its own filesystem if you can.

---

## 3. Scrape config

[Part 2, step 3](/fields/devops/victoriametrics/single-node-in-ten-minutes.md#step-3-what-to-scrape).

```bash
cat > /etc/victoriametrics/scrape.yml <<'EOF'
global:
  scrape_interval: 30s
scrape_configs:
  - job_name: node
    static_configs:
      - targets: ['10.0.0.11:9100', '10.0.0.12:9100']
  - job_name: victoriametrics
    static_configs:
      - targets: ['10.0.0.5:8428']
EOF
victoria-metrics-prod -promscrape.config=/etc/victoriametrics/scrape.yml -promscrape.config.dryRun -loggerLevel=ERROR
echo "exit=$?"
```

Expected: no output, `exit=0`. A broken file exits 255 with the line number.

---

## 4. The service

[Part 2, steps 5 and 6](/fields/devops/victoriametrics/single-node-in-ten-minutes.md#step-5-the-systemd-unit).

```bash
cat > /etc/systemd/system/victoriametrics.service <<'EOF'
[Unit]
Description=VictoriaMetrics single-node
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=victoriametrics
Group=victoriametrics
StateDirectory=victoriametrics
ExecStart=/usr/local/bin/victoria-metrics-prod \
  -storageDataPath=/var/lib/victoriametrics \
  -retentionPeriod=90d \
  -httpListenAddr=10.0.0.5:8428 \
  -promscrape.config=/etc/victoriametrics/scrape.yml \
  -deleteAuthKey=file:///etc/victoriametrics/delete.key \
  -snapshotAuthKey=file:///etc/victoriametrics/snapshot.key
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

# Lint by output: systemd-analyze verify exits 0 even when it finds a bad value
out=$(systemd-analyze verify /etc/systemd/system/victoriametrics.service 2>&1)
[ -z "$out" ] && echo "LINT OK" || { echo "LINT FAIL: $out"; false; }

systemctl daemon-reload
systemctl enable --now victoriametrics
curl -fsS http://10.0.0.5:8428/health; echo " exit=$?"
curl -s http://10.0.0.5:8428/api/v1/targets | python3 -c '
import json, sys
for t in json.load(sys.stdin)["data"]["activeTargets"]:
    print(t["labels"]["job"], t["health"], t.get("lastError", ""))'
```

Expected: `LINT OK`, `OK exit=0`, then every job `up`. A target can show `down` with an empty `lastError` for up to one scrape interval after start; that means "not tried yet". The newest 30 s of data are hidden from queries by `-search.latencyOffset`, so a query straight after start can come back empty.

---

## 5. Reload safely

[Part 2](/fields/devops/victoriametrics/single-node-in-ten-minutes.md#changing-config-without-a-surprise). A HUP with a broken file keeps the old config and only logs an error. So: check, reload, confirm.

```bash
victoria-metrics-prod -promscrape.config=/etc/victoriametrics/scrape.yml -promscrape.config.dryRun -loggerLevel=ERROR \
  && systemctl reload victoriametrics
curl -s http://10.0.0.5:8428/metrics | grep '^vm_promscrape_config_last_reload_successful '
```

Expected: `vm_promscrape_config_last_reload_successful 1`. Flags need a restart, not a reload.

---

## 6. vmagent at the edge

[Part 3](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md#run-it). Buffers on disk while the database is unreachable.

```bash
vmagent-prod \
  -promscrape.config=/etc/vmagent/scrape.yml \
  -remoteWrite.url=http://10.0.0.5:8428/api/v1/write \
  -remoteWrite.tmpDataPath=/var/lib/vmagent \
  -remoteWrite.queuePath=/var/lib/vmagent/queue-central \
  -remoteWrite.maxDiskUsagePerURL=4GiB \
  -httpListenAddr=10.0.1.2:8429
```

- **Always** set `-remoteWrite.queuePath` (v1.156.0+), one per `-remoteWrite.url`, in the same order. Without it, editing or reordering a URL makes vmagent delete its queue as "dangling" on the next start. Before v1.156.0, use `-remoteWrite.keepDanglingQueues` and drain the queue before touching a URL.
- Each queue path is used by one URL only; vmagent deletes the contents of a directory that isn't a valid queue.
- Size the cap from what you actually send, here for 6 hours:

```text
sum(rate(vmagent_remotewrite_bytes_sent_total[1h])) by (instance, url) * 6h / 1Gi
```

- Check the backlog before any URL change: `vmagent_remotewrite_pending_data_bytes` should be `0`.

---

## 7. Retention and disk

[Part 4](/fields/devops/victoriametrics/retention-disk-and-backups.md#what-retention-really-deletes-and-when).

| Fact | Value |
| --- | --- |
| Default `-retentionPeriod` | `1M` = 31 days. Units `h d w M y`; bare number = months; lowercase `m` is refused |
| Disk peaks at | Retention **plus one month** (monthly partitions are deleted on the 1st) |
| Size the disk | Run one real day, then `disk = day × (retention days + 31) ÷ 0.8` |
| Disk full | Read-only below `-storage.minFreeDiskSpaceBytes` (default 100 MB). `/health` still says `OK`. Watch `vm_storage_is_read_only` |
| Monitor it from | **Another** instance. A read-only database can't store its own metrics |

Lowering retention deletes data with no undo: back up first, change one node, watch `vm_data_size_bytes`, then the rest.

---

## 8. Backups

[Part 4](/fields/devops/victoriametrics/retention-disk-and-backups.md#an-hourly-job-you-can-leave-running). Hourly incremental into `latest/`, daily server-side copy into a dated folder, 14 days kept.

```bash
install -d -o victoriametrics -g victoriametrics -m 0750 /backup/victoriametrics

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
runuser -u victoriametrics -- /usr/local/sbin/vm-backup; echo "exit=$?"

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
systemctl list-timers vm-backup.timer
```

Expected: `vm-backup: ok`, `exit=0`, and the next run at five past the hour. `fs://` on a local disk isn't a backup of the machine: point `DST` at another host, or use `s3://` with `-credsFilePath`. Since v1.122.0, `-snapshotsMaxAge` (default `3d`) removes snapshots an interrupted backup left behind; on older versions set it yourself.

---

## 9. Prove the backup

[Part 4](/fields/devops/victoriametrics/retention-disk-and-backups.md#proving-the-backup). Monthly. vmrestore makes the target match the backup exactly, so never point it at a live data directory (it refuses while the lock is held).

```bash
vmrestore-prod -src=fs:///backup/victoriametrics/$(date +%Y%m%d) \
  -storageDataPath=/srv/restore-test -loggerLevel=ERROR
victoria-metrics-prod -storageDataPath=/srv/restore-test -httpListenAddr=127.0.0.1:8435 &
curl -s http://127.0.0.1:8435/api/v1/query \
  --data-urlencode 'query=count(count_over_time({job="node"}[2h]))'
```

Expected: the same count as the same query on the live database.

---

## 10. Alerts with tests

[Part 5](/fields/devops/victoriametrics/metricsql-and-vmalert.md#three-rules-that-watch-the-watchers). Save the rules as `/etc/vmalert/rules.yml`:

```yaml
groups:
  - name: vm-self
    interval: 30s
    rules:
      - alert: VMStorageReadOnly
        expr: vm_storage_is_read_only == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "VictoriaMetrics at {{ $labels.instance }} is read-only and rejecting writes"
      - alert: VMScrapeConfigReloadFailed
        expr: vm_promscrape_config_last_reload_successful == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Scrape config reload failed on {{ $labels.instance }}; old config still active"
      - alert: VMAgentQueueBacklog
        expr: sum by (instance) (vmagent_remotewrite_pending_data_bytes) > 100e6
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "vmagent {{ $labels.instance }} has over 100 MB waiting to be sent"
```

The test file `rules_test.yml` and the mutation script `check-rules.sh` are printed in full in [Tests that can fail](/fields/devops/victoriametrics/metricsql-and-vmalert.md#tests-that-can-fail). Run both:

```bash
vmalert-tool-prod unittest --files rules_test.yml; echo "exit=$?"
./check-rules.sh; echo "exit=$?"
```

Expected: `SUCCESS`, then `PASS  real rules` and one `PASS  mutant caught` per mutant, `exit=0`. Three things that made our own tests lie:

- `rule_files` paths are relative to the **test file**, not your shell.
- Put each "should not fire" check at the moment a broken rule **would** fire.
- vmalert-tool ignores a group's `interval` and uses the file's `evaluation_interval`: set them equal.

---

## 11. Run vmalert

[Part 5](/fields/devops/victoriametrics/metricsql-and-vmalert.md#run-vmalert). On the **monitoring** instance, not the one being watched.

```bash
vmalert-prod -rule=/etc/vmalert/rules.yml -dryRun; echo "exit=$?"
vmalert-prod \
  -rule=/etc/vmalert/rules.yml \
  -datasource.url=http://10.0.0.6:8428 \
  -remoteWrite.url=http://10.0.0.6:8428 \
  -notifier.url=http://10.0.0.6:9093 \
  -httpListenAddr=10.0.0.6:8880
curl -s http://10.0.0.6:8880/api/v1/alerts
```

Expected: `exit=0` from the dry run. Firing alerts also appear as `ALERTS{alertstate="firing"}` series in the monitoring instance.

---

## Quick reference

| Task | Command or setting |
| --- | --- |
| Health (process only, not writes) | `curl http://10.0.0.5:8428/health` |
| Is it actually storing? | `vm_storage_is_read_only == 0` |
| Did the last reload work? | `vm_promscrape_config_last_reload_successful == 1` |
| vmagent backlog | `vmagent_remotewrite_pending_data_bytes` |
| Data on disk | `vm_data_size_bytes` |
| Query UI | `http://10.0.0.5:8428/vmui/` |
| Delete series (needs the delete key) | `curl -X POST 'http://10.0.0.5:8428/api/v1/admin/tsdb/delete_series?authKey=...' --data-urlencode 'match[]=...'` |
| Expose to untrusted clients | Only through **vmauth**, never directly |
| `increase()` disagrees with Prometheus | Expected: VictoriaMetrics doesn't extrapolate. See [part 5](/fields/devops/victoriametrics/metricsql-and-vmalert.md#same-data-two-answers) |

**Takeaway:** verify the binary, run it as its own user on an internal address with admin keys, reload by check-reload-confirm, buffer with a pinned vmagent queue, size the disk for retention plus a month, back up hourly and restore monthly, and alert from a second instance with rules whose tests can fail.

**Series index:** [VictoriaMetrics](/fields/devops/victoriametrics/README.md). To scrape Slurm into it, see [Slurm Metrics Without an Exporter](/fields/schedulers/slurm-ai-clusters/metrics-openmetrics.md).

---

## References

- [VictoriaMetrics single-node docs](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/): flags, retention, capacity planning, security.
- [vmagent](https://docs.victoriametrics.com/victoriametrics/vmagent/): remote write, on-disk queue, `-remoteWrite.queuePath`.
- [vmbackup](https://docs.victoriametrics.com/victoriametrics/vmbackup/) and [vmrestore](https://docs.victoriametrics.com/victoriametrics/vmrestore/): snapshots, smart backups, restores.
- [vmalert](https://docs.victoriametrics.com/victoriametrics/vmalert/) and [vmalert-tool](https://docs.victoriametrics.com/victoriametrics/vmalert-tool/): rules and unit tests.
- [VictoriaMetrics releases](https://github.com/VictoriaMetrics/VictoriaMetrics/releases): tarballs and checksums.