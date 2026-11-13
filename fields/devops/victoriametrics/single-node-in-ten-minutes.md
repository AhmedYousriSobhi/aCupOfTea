
# A Single Node You Can Trust: Installing VictoriaMetrics Properly

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The Prometheus That Ate the Head Node: Why VictoriaMetrics](/fields/devops/victoriametrics/why-victoriametrics.md)  ·  **See also:** [VictoriaMetrics Cheatsheet: Every Step from the Series](/fields/devops/victoriametrics/cheatsheet.md)  ·  **Read next:** [vmagent and the Network Blip: Keeping Metrics Through an Outage](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md), [Retention, Full Disks and Backups: Looking After the Data Once It Lands](/fields/devops/victoriametrics/retention-disk-and-backups.md), [MetricsQL Surprises and Alerts You Can Test](/fields/devops/victoriametrics/metricsql-and-vmalert.md), [Slurm Metrics Without an Exporter: OpenMetrics into VictoriaMetrics](/fields/schedulers/slurm-ai-clusters/metrics-openmetrics.md)

</div>


> **Part 2 of the [VictoriaMetrics series](/fields/devops/victoriametrics/README.md).** [Part 1](/fields/devops/victoriametrics/why-victoriametrics.md) explained what VictoriaMetrics is. By the end of this page you'll have a single node running under systemd, scraping targets, reloading config without surprises, and refusing to delete data for strangers.

- [A Single Node You Can Trust: Installing VictoriaMetrics Properly](#a-single-node-you-can-trust-installing-victoriametrics-properly)
  - [The intern and the empty dashboard](#the-intern-and-the-empty-dashboard)
  - [Before you start](#before-you-start)
  - [Step 1: download and verify](#step-1-download-and-verify)
  - [Step 2: a user and two directories](#step-2-a-user-and-two-directories)
  - [Step 3: what to scrape](#step-3-what-to-scrape)
  - [Step 4: two admin keys](#step-4-two-admin-keys)
  - [Step 5: the systemd unit](#step-5-the-systemd-unit)
  - [Step 6: start it and check it](#step-6-start-it-and-check-it)
  - [Two things that look broken but aren't](#two-things-that-look-broken-but-arent)
  - [Changing config without a surprise](#changing-config-without-a-surprise)
  - [Why the admin keys matter](#why-the-admin-keys-matter)
  - [Back to the intern](#back-to-the-intern)
  - [References](#references)

---

## The intern and the empty dashboard

An intern is cleaning up "test metrics" from Grafana. They find a VictoriaMetrics URL, read that `/api/v1/admin/tsdb/delete_series` deletes series, and send it a match for everything starting with `node_`. It works on the first try. No password, no prompt. Every node metric for the whole retention period is gone.

Nothing about that is a bug. It's the default. This page installs VictoriaMetrics the way you'd want it on a shared network: verified binary, its own user, a bound address, and keys on the endpoints that can destroy or copy data.

---

## Before you start

> [!NOTE]
> Written against VictoriaMetrics **v1.156.0**. Every step was run on a throwaway Ubuntu 24.04.5 sandbox (Linux 6.18, systemd 255) with node_exporter 1.12.1 as a target. systemd wasn't running there, so the unit in step 5 was linted with `systemd-analyze verify` and its exact command line was run by hand as the service user, but `systemctl start` itself wasn't run.

You need: a Linux x86-64 host, root, and outbound HTTPS to GitHub. The examples use `10.0.0.5` as the host's internal address. Replace it with yours.

---

## Step 1: download and verify

Pin the version, download the tarball and its checksum file, and check one against the other before you run anything.

```bash
VM_VERSION=v1.156.0
cd /tmp
curl -fsSLO https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VM_VERSION}/victoria-metrics-linux-amd64-${VM_VERSION}.tar.gz
curl -fsSLO https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VM_VERSION}/victoria-metrics-linux-amd64-${VM_VERSION}_checksums.txt
grep "victoria-metrics-linux-amd64-${VM_VERSION}.tar.gz" victoria-metrics-linux-amd64-${VM_VERSION}_checksums.txt | sha256sum --check
```

Success looks like this, with exit code 0:

```text
victoria-metrics-linux-amd64-v1.156.0.tar.gz: OK
```

We also appended one line of junk to the tarball to prove the check bites. It printed `FAILED` and exited 1:

```text
victoria-metrics-linux-amd64-v1.156.0.tar.gz: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
```

Then install the binary and confirm the version:

```bash
tar -xzf victoria-metrics-linux-amd64-${VM_VERSION}.tar.gz
install -m 0755 victoria-metrics-prod /usr/local/bin/victoria-metrics-prod
/usr/local/bin/victoria-metrics-prod --version
```

```text
victoria-metrics-20261106-174742-tags-v1.156.0-0-g0c1bf87a0c
```

> [!TIP]
> The binary is called `victoria-metrics-prod`, not `victoria-metrics`. Keep the name; the docs and every example online use it.

---

## Step 2: a user and two directories

The database should own its data and nothing else.

```bash
useradd --system --no-create-home --shell /usr/sbin/nologin victoriametrics
install -d -o victoriametrics -g victoriametrics -m 0750 /var/lib/victoriametrics
install -d -m 0755 /etc/victoriametrics
```

Success: `ls -ld /var/lib/victoriametrics` shows `drwxr-x--- victoriametrics victoriametrics`.

Put `/var/lib/victoriametrics` on its own filesystem if you can. When the disk fills, you want the database to stop, not the whole host. Part 4 covers what "stop" means here, and it isn't what you'd guess.

---

## Step 3: what to scrape

Single-node VictoriaMetrics reads a normal Prometheus `scrape_configs` file. Start with node_exporter and the database itself:

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
```

Check the file before the database ever sees it:

```bash
/usr/local/bin/victoria-metrics-prod -promscrape.config=/etc/victoriametrics/scrape.yml \
  -promscrape.config.dryRun -loggerLevel=ERROR
echo "exit=$?"
```

A good file prints nothing and exits 0. A broken one (we dropped a colon) exits 255 with the line number:

```text
fatal ... error when checking -promscrape.config: cannot parse Prometheus config from "scrape.yml": cannot unmarshal data: yaml: line 15: could not find expected ':'
```

Keep this command. You'll use it before every reload.

---

## Step 4: two admin keys

Several endpoints can delete or copy your data, and each can be protected by a key. Make two: one for deleting series, one for snapshots. They're separate on purpose. The backup tool in part 4 needs the snapshot key, and it prints that key in its logs, so a leaked backup log mustn't be able to delete anything.

```bash
for k in delete snapshot; do
  openssl rand -hex 24 | install -m 0640 -g victoriametrics /dev/stdin /etc/victoriametrics/$k.key
done
```

Success: `ls -l /etc/victoriametrics/` shows both files as `-rw-r----- root victoriametrics`. The trailing newline that `openssl` writes is fine; the keys still matched in testing. We also checked they don't cross: the delete key got 401 on `/snapshot/list`, and the snapshot key got 401 on the delete endpoint.

---

## Step 5: the systemd unit

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
```

What each choice buys you:

| Line | Why |
| --- | --- |
| `-retentionPeriod=90d` | The default is 31 days. Say what you mean, and read part 4 before you pick |
| `-httpListenAddr=10.0.0.5:8428` | Without it, the database binds `:8428`, every interface. Bind to the internal one |
| `-deleteAuthKey`, `-snapshotAuthKey` | Closes the delete and snapshot endpoints to anyone without the right key |
| `ExecReload=... -HUP` | A HUP re-reads the scrape file. Flags still need a restart |
| `LimitNOFILE=1048576` | Raising the open-files limit is the one OS tweak the docs' tuning section recommends |

Now lint it. Here's a trap we hit: `systemd-analyze verify` (systemd 255) **exits 0 even when it finds a bad value**. With `Restart=on-falure` it printed a warning and still returned 0:

```text
victoriametrics.service:19: Failed to parse service restart specifier, ignoring: on-falure
```

So check its output, not its exit code:

```bash
out=$(systemd-analyze verify /etc/systemd/system/victoriametrics.service 2>&1)
[ -z "$out" ] && echo "LINT OK" || { echo "LINT FAIL: $out"; false; }
```

Success: `LINT OK`. On the typo'd copy, the same check printed `LINT FAIL` and returned non-zero.

---

## Step 6: start it and check it

```bash
systemctl daemon-reload
systemctl enable --now victoriametrics
curl -fsS http://10.0.0.5:8428/health; echo " exit=$?"
```

Success: `OK exit=0`. Then look at the targets:

```bash
curl -s http://10.0.0.5:8428/api/v1/targets | python3 -c '
import json, sys
for t in json.load(sys.stdin)["data"]["activeTargets"]:
    print(t["labels"]["job"], t["health"], t.get("lastError", ""))'
```

```text
victoriametrics up
node up
```

And ask a real question:

```bash
curl -s http://10.0.0.5:8428/api/v1/query --data-urlencode 'query=up'
```

`vmui`, the built-in query UI, lives at `http://10.0.0.5:8428/vmui/` if you'd rather click.

---

## Two things that look broken but aren't

Both showed up in the lab within the first minute, and both make people restart things that are fine.

**A new target shows `down` before its first scrape.** Right after start, `/api/v1/targets` showed `node down` with an empty `lastError`. Twenty seconds later it was `up`. Scrapes are spread out over the interval, so the first one can take up to one `scrape_interval`. An empty `lastError` means "not tried yet". A real failure always carries a message.

**A query returns nothing for the newest data.** Our first `up` query came back empty even though the targets had just been scraped:

```text
{"status":"success","data":{"resultType":"vector","result":[]}, ...}
```

That's `-search.latencyOffset`, which defaults to 30 seconds: points younger than that are hidden from queries so you don't see half-written data. The same query with `latency_offset=1s` returned both series. Leave the default alone; it's there for a reason. Just know it exists when you test with `curl` straight after a start.

---

## Changing config without a surprise

Here's the trap. When you HUP with a broken scrape file, VictoriaMetrics logs an error and **keeps running the old config**:

```text
error ... cannot read "scrape.yml" on SIGHUP: ... yaml: line 15: could not find expected ':'; ... continuing with the previous config
```

The process stays up, targets stay the same, and nobody notices your new target was never added. So reload in three steps: check, reload, confirm.

1. **Check** the file with the dry run from step 3. Stop if the exit code isn't 0.
2. **Reload:** `systemctl reload victoriametrics`.
3. **Confirm** the reload took:

```bash
curl -s http://10.0.0.5:8428/metrics | grep '^vm_promscrape_config_last_reload_successful '
```

```text
vm_promscrape_config_last_reload_successful 1
```

In the lab this metric went to `0` after the bad HUP and back to `1` after a good one. Part 5 turns it into an alert.

> [!NOTE]
> `systemctl reload` wasn't run in the lab (no systemd). We sent `kill -HUP` directly, which is what the unit's `ExecReload` does.

---

## Why the admin keys matter

Back to the intern. Without `-deleteAuthKey`, we imported a scratch series and deleted it with one unauthenticated request. HTTP 204, series gone:

```bash
curl -s -X POST 'http://127.0.0.1:8428/api/v1/admin/tsdb/delete_series' \
  --data-urlencode 'match[]=scratch_metric' -w '%{http_code}\n'
```

```text
204
```

With the key set, the same request was refused, and so was a wrong key:

```text
Expected to receive non-empty authKey when -deleteAuthKey is set     (401)
The provided authKey doesn't match -deleteAuthKey                    (401)
```

Only `?authKey=<the key>` got 204. `/snapshot/create` behaved the same way with `-snapshotAuthKey`.

The keys protect a handful of dangerous endpoints, and the server itself is careful with them: its startup log prints `-snapshotAuthKey="secret"`, not the value. They don't protect queries or ingestion. The docs list more endpoint keys (`-reloadAuthKey`, `-configAuthKey`, `-flagsAuthKey`, `-pprofAuthKey` and others) and say plainly that every component belongs in a private network, with **vmauth** in front of anything that untrusted clients can reach. Rule of thumb: **bind to the inside, key the dangerous doors, proxy everything else.**

---

## Back to the intern

Same intern, same cleanup idea, same Friday. This time the database was installed with this page:

| What the intern tries | What happens now | Which step stopped it |
| --- | --- | --- |
| Sends `delete_series` for `node_.*` with no key | `401 Expected to receive non-empty authKey when -deleteAuthKey is set` | Step 4 and step 5 |
| Goes looking for the key | `/etc/victoriametrics/delete.key` is `-rw-r-----`, readable by root and the `victoriametrics` group only | Step 4 |
| Tries the snapshot key from a backup log | `401`: it can take snapshots, not delete | Step 4 |
| Connects from a network that shouldn't reach it | Nothing listens there: the database is bound to `10.0.0.5`, and anything wider goes through vmauth | Step 5 |
| Someone with root deletes the series anyway | The hourly backup from [part 4](/fields/devops/victoriametrics/retention-disk-and-backups.md) restores them | Part 4 |

The cleanup can still happen. The intern asks, someone holding the delete key runs it, on purpose, with a match they've read twice. Deleting history should take a decision, not just a `curl`.

And when the same intern adds a new target with a typo in the YAML, the dry run catches it before the reload, and the reload metric catches it if they skip the dry run.

**Takeaway:** a verified binary, its own user, a bound address, admin keys and a check-reload-confirm habit turn a "just run it" database into one you can leave on a shared network.

**Next:** [Part 3, vmagent and the Network Blip](/fields/devops/victoriametrics/vmagent-and-the-network-blip.md), moves scraping to the edge and keeps data through an outage.

---

## References

- [VictoriaMetrics single-node docs](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/): how to start, scraping with `-promscrape.config`, how to apply new config, security recommendations and protected endpoints, deleting series, snapshots.
- [Common command-line flags](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/#list-of-command-line-flags): `-promscrape.config.dryRun`, `-search.latencyOffset` (default 30s), `-deleteAuthKey`, `-snapshotAuthKey`, `-httpListenAddr`.
- [VictoriaMetrics v1.156.0 release](https://github.com/VictoriaMetrics/VictoriaMetrics/releases/tag/v1.156.0): tarballs and checksum files.
- [vmui](https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/#vmui): the built-in query UI.
- [vmauth](https://docs.victoriametrics.com/victoriametrics/vmauth/): the auth proxy recommended in front of VictoriaMetrics.
- [systemd-analyze(1)](https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html): the `verify` command.
- [node_exporter](https://github.com/prometheus/node_exporter): the example target.