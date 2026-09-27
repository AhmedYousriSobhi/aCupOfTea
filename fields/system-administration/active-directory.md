# Active Directory — The Senior Engineer's Reference Card
> Scope: history & motivation → internals → PAM/NSS primer → build → Linux/HPC integration → debugging
> Assumes: zero prior PAM/NSS knowledge, solid Linux sysadmin background

---

## 0. Brief History — Why Any of This Exists

Understanding *why* LDAP and AD look the way they do is worth more than memorizing their syntax. Every weird design choice below is a scar tissue from a real problem.

Picture the 1980s: a technological landscape where telecom gaints and international standards bodies dreamed of a unified, global digital telephone book for every human, server, and toaster on planet Earth.

### 0.1 The X.500 disaster (1980s)

- The ITU/ISO designed **X.500**: a grand, formally-specified global directory standard — think "DNS for *everything about every person and object on Earth*."
- Access protocol was **DAP** (Directory Access Protocol) — riding on the full OSI network stack, not TCP/IP.
- It was enormous, over-engineered, and required heavyweight OSI infrastructure almost nobody actually ran. It mostly died in production.
- In practice, running the OSI stack required specialized, enterprise-grade gear and networking wizardry that ordinary organizations simply didn't have or want. X.500 was too heavy to fly, too expensive to maintain, and it mostly crashed and burned in real-world production. It was a glorious disaster.

### 0.2 LDAP — the "lightweight" escape hatch (1993, University of Michigan)

- **LDAP = Lightweight Directory Access Protocol.** The word "lightweight" is not marketing — it specifically means *"X.500's data model, but spoken over plain TCP/IP instead of OSI, with a simplified encoding."*
- It kept X.500's tree-shaped data model (the DN/`CN=`/`OU=`/`DC=` hierarchy you see today) but threw out the transport baggage.
- LDAP itself is **only a protocol** — a wire format and a set of operations (`bind`, `search`, `add`, `modify`, `delete`, `compare`). It does not mandate *how* the server stores data, *how* it replicates, or *how* it authenticates beyond simple bind/SASL. This matters a lot in §0.4.

### 0.3 What was missing before AD, on both sides of the fence

| Problem (pre-1999) | Unix world's answer | Windows world's answer |
|---|---|---|
| Central user database across many machines | **NIS** ("Yellow Pages") — flat maps of `/etc/passwd`, broadcast over the LAN | **NT Domains** — single PDC + BDC replicas, flat namespace |
| Security of that database | NIS sent password hashes essentially in the clear, no real access control, trivially spoofable | NTLM — password-equivalent hash auth, no ticket expiry model, vulnerable to relay/pass-the-hash |
| Scaling to thousands of objects, sites, org units | NIS had no hierarchy — one flat map per domain | NT4 domain size was capped in practice (~40,000 objects) and had no OU concept, one write-master (PDC) |
| Delegated administration | Essentially none | Essentially none |

Both ecosystems hit a wall around the same time: **flat, single-master, weakly-secured directories don't scale to a multinational company or a large campus.**

### 0.4 Microsoft's answer: build a product on top of *other people's* protocols

This is the crux of the confusion most people have, so say it plainly:

> **Active Directory is not a protocol. It is Microsoft's directory *server product*, and LDAP is merely the interface it exposes for reading/writing objects.** AD bolts LDAP together with Kerberos (borrowed from MIT, not invented by Microsoft), DNS (as the service locator), and a proprietary multi-master replication engine (DRS/RPC) that LDAP itself has no opinion about.

Released with Windows 2000 Server, AD's actual motivation was:
1. Replace NT4's flat, single-master domain model with a **hierarchical, multi-master** one (any DC can accept writes).
2. Replace NTLM with **Kerberos** as the primary auth protocol — real ticket expiry, mutual authentication, no password-equivalent secrets crossing the wire.
3. Use **DNS** — an open standard already being deployed everywhere in the DNS/Internet boom of the late 90s — as the mechanism clients use to *find* a domain controller, instead of NetBIOS broadcast/WINS.
4. Expose it all over **LDAP** so that non-Windows tools/scripts could still query it without needing Microsoft-proprietary APIs.

So: **LDAP is the "SQL" of directories — a query language/protocol implemented by many products (OpenLDAP, 389 Directory Server, AD, Oracle Internet Directory...). AD is one specific, commercial, Windows-native implementation that happens to speak LDAP as one of its four faces.**

### 0.5 The direct explicit comparison

| | **LDAP (the protocol)** | **Active Directory (the product)** |
|---|---|---|
| What it is | An open protocol spec (RFC 4511 etc.) | A Microsoft server product |
| Who "owns" it | IETF, open standard | Microsoft |
| Implementations | OpenLDAP, 389DS, ApacheDS, AD, Oracle Unified Directory... | Windows Server AD DS specifically |
| Authentication | LDAP simple bind (plaintext-ish, or SASL) only | Kerberos primarily; LDAP simple bind supported too |
| Replication | **Not defined by LDAP at all** — up to the implementer | Proprietary multi-master DRS/RPC replication |
| Schema | Extensible, implementation-specific | Extensible, but changes are forest-wide and largely irreversible |
| Client discovery | You must be told the server address | Self-discovering via **DNS SRV records** |
| Group Policy, SYSVOL, computer objects | Doesn't exist — not an LDAP concept at all | Core AD feature |
| Can you run AD without LDAP? | N/A | No — LDAP is how almost everything reads/writes AD objects |
| Can you use LDAP without AD? | Yes — that's the majority of LDAP deployments (OpenLDAP on Linux, etc.) | N/A |

**One-line summary:** *querying AD with `ldapsearch` works because AD speaks LDAP, not because AD "is" LDAP — the same way you can `curl` a REST API on almost any web server without that server "being" HTTP.*

---

## 1. What AD Actually *Is* Under the Hood

Active Directory is four protocols/services wearing a trench coat:

| Layer | Protocol/Port | Job |
|---|---|---|
| Directory store | LDAP (389/636) | Object read/write — users, groups, computers, GPOs |
| Authentication | Kerberos (88) | Ticket-based auth, mutual, no password over wire |
| Locator service | DNS (53) — **SRV records** | How clients *find* a DC in the first place |
| Replication | RPC/DRS (135 + dynamic, or 445 SMB) | Multi-master sync between Domain Controllers |
| File replication | SYSVOL via DFS-R | GPOs and login scripts replicated to every DC |

<details>
<summary><b>The database itself</b> (click to expand)</summary>

- Backing store: `NTDS.dit` — an ESE (Jet Blue) database, same engine family as Exchange.
- Every object gets a **GUID** (never changes) and a **DN** (Distinguished Name, changes if moved/renamed).
- Schema is itself stored as objects in the `CN=Schema,CN=Configuration,...` partition — this is why extending AD schema (e.g. for RFC2307 `uidNumber`/`gidNumber`) is a *replicated, forest-wide, irreversible* operation.
- Three NDS partitions per DC: **Schema**, **Configuration** (forest-wide topology), **Domain** (the actual objects) — plus optional **Application partitions** (used by DNS).

</details>

### 1.1 Kerberos flow (the part that actually breaks in practice)

Named after Cerberus, the three-headed dog guarding the underworld — three parties involved in every exchange: client, KDC, service. Invented at MIT in the 1980s for Project Athena, long before AD existed; Microsoft adopted it wholesale (with proprietary extensions like PAC for authorization data) rather than inventing a new auth protocol.

```
 Client                     KDC (=DC)                    Service (e.g. sshd)
   |--- AS-REQ (I'm ahmed) ----->|
   |<-- AS-REP (TGT, encrypted) -|      Step 1: prove identity, get TGT
   |
   |--- TGS-REQ (TGT + SPN) ---->|
   |<-- TGS-REP (service ticket)-|      Step 2: exchange TGT for a service ticket
   |
   |--- AP-REQ (service ticket) -------------------------->|
   |<-------------------------- AP-REP (mutual auth) ------|
```

- **AS** = Authentication Service (proves who you are, issues a TGT — Ticket Granting Ticket)
- **TGS** = Ticket Granting Service (exchanges a TGT for a ticket to a *specific* service, identified by an **SPN** — Service Principal Name, e.g. `host/gpu209-06.hpc.internal`)
- **Why this is better than NTLM/passwords-over-wire:** the password itself never crosses the network, even encrypted. It's used locally to derive a key that decrypts the TGT — if you don't have the right password, decryption produces garbage and you silently fail, no secret is ever transmitted to attack.

> ⚠️ **Everything here is time-stamped and encrypted with symmetric keys derived from passwords.**
> Kerberos has a hard **5-minute clock skew tolerance** by default (this exists specifically to make replay attacks with a stolen ticket harder). This single fact causes more AD outages than every other cause combined — remember it, it comes back in §6.

### 1.2 FSMO roles — AD is multi-master, *except* for 5 operations

AD's multi-master design (any DC accepts writes) is efficient but creates a problem: some operations are fundamentally *not* safe to do from two places at once (e.g. two DCs independently handing out the same unique ID). Rather than lock the whole directory, Microsoft carved out exactly five narrow operations that get a single-master ("Flexible Single Master Operation") owner:

| Role | Scope | Why it can't be multi-master |
|---|---|---|
| Schema Master | Forest | Schema changes must be serialized — two DCs adding conflicting attribute definitions simultaneously would corrupt the schema |
| Domain Naming Master | Forest | Adding/removing domains — prevents two DCs creating domains with colliding names |
| RID Master | Domain | Hands out blocks of RIDs (Relative IDs, the tail end of a SID) so no two DCs ever mint the same SID for different users |
| PDC Emulator | Domain | Time sync root for the whole domain, password-change authority, legacy NT4 compatibility target |
| Infrastructure Master | Domain | Fixes stale cross-domain group references (matters only in multi-domain forests) |

```powershell
# Verify which DC holds which role
netdom query fsmo
```

---

## 2. PAM & NSS — Ground-Up Primer (Linux side, required before §5)

Everything downstream depends on these two subsystems, so build the mental model properly before touching SSSD.

### 2.1 The problem they each solve

Before PAM/NSS existed, every Linux/Unix program that needed to check a password (`login`, `su`, `sshd`, `passwd`...) had its own hardcoded logic for reading `/etc/passwd` and `/etc/shadow`. If you wanted to add a new auth source — say, a fingerprint reader, or a remote directory — you had to **recompile every single program** that did authentication. That's obviously untenable.

**PAM and NSS split "identity" into two separate, independent questions**, each solved by a pluggable framework:

| Question | Subsystem | Example |
|---|---|---|
| "**Who** is `ahmed`, and what's his UID/GID/home dir/shell?" | **NSS** (Name Service Switch) | `getent passwd ahmed` |
| "**Is** this really `ahmed` — does the password/ticket/fingerprint check out, and is he *allowed* to log in here right now?" | **PAM** (Pluggable Authentication Modules) | `sshd` calling into PAM during login |

These are genuinely orthogonal. You can have NSS resolve a user's identity from AD while PAM authenticates them against a totally different source (or vice versa) — in practice SSSD provides both, but the separation is why the config lives in two different files.

### 2.2 NSS — Name Service Switch

Glibc, at its core, offers C library calls like `getpwnam()`, `getgrnam()`, `gethostbyname()`. NSS is the mechanism that lets glibc decide, **at runtime, without recompiling anything**, *where* to look up the answer to those calls.

`/etc/nsswitch.conf`:
```
passwd:     files sss
group:      files sss
shadow:     files sss
hosts:      files dns
```

Read left to right: for `passwd` lookups, check local `/etc/passwd` (**files**) first, then fall through to **sss** (SSSD, which in turn asks AD over LDAP). This is why a *local* Linux account with the same username as an AD account can silently "win" and mask the AD identity — a classic gotcha.

Each backend (`files`, `sss`, `dns`, `nis`...) is a shared library (`libnss_sss.so.2` etc.) — that's the "plugin" in "Name Service Switch." NSS itself does zero networking; it's a dispatcher.

```bash
# See exactly which NSS module answered, and how long it took
getent passwd ahmed
# Confirm the shared library actually exists and is loaded
ldd $(which getent) | grep nss   # (illustrative — real check is via nsswitch, not getent's own linking)
```

### 2.3 PAM — Pluggable Authentication Modules

PAM sits *underneath* login-capable programs (`login`, `sshd`, `sudo`, `su`, `gdm`...) and is configured per-service in `/etc/pam.d/<service>`, e.g. `/etc/pam.d/sshd`.

Each line has a **type**, a **control flag**, and a **module**:

```
auth     required     pam_sss.so
account  required     pam_sss.so
password sufficient   pam_sss.so
session  optional     pam_sss.so
```

| Type | Question it answers |
|---|---|
| `auth` | Is the credential (password/ticket) valid? |
| `account` | Is the account allowed to log in *right now*? (expired, locked, outside allowed hours, group-restricted...) |
| `password` | Handles password *changes* |
| `session` | Runs setup/teardown around the session (mounting home dirs, writing login records, setting up Kerberos credential cache...) |

| Control flag | Behavior on failure |
|---|---|
| `required` | Must succeed; continues evaluating the rest of the stack anyway, but the overall result is failure — used so an attacker can't tell *which* module in the stack rejected them |
| `requisite` | Must succeed; fails immediately, stack stops right there |
| `sufficient` | If it succeeds, stop immediately and grant — skips remaining modules |
| `optional` | Result mostly ignored unless it's the only module in the stack |

**This is why `id ahmed` can work (NSS is happy) while `ssh ahmed@host` still fails (PAM's `account` phase is rejecting him, or GSSAPI isn't even reaching PAM)** — they're genuinely different subsystems being asked genuinely different questions, and diagnosing "AD login doesn't work" always means figuring out *which* of the two is at fault first.

### 2.4 Where SSSD fits

SSSD (System Security Services Daemon) is a **single background daemon that implements both an NSS module and a PAM module**, and internally does the actual Kerberos/LDAP network chatter with AD, plus caching so logins survive a brief DC outage. Before SSSD existed, people ran `pam_krb5` + `pam_ldap` + `nss_ldap` as three separate, uncoordinated pieces — SSSD unifies them and adds an offline cache, which is why it's now the standard.

```
 login/sshd
     │
   PAM  ──────────────►  pam_sss.so   (authentication — "auth" and "account" phases)
     │
   NSS  ──────────────►  nss_sss.so   (getpwnam/getgrnam resolution)
     │
   SSSD daemon ─────────► caches, talks Kerberos + LDAP to the DC, handles offline mode
```

---

## 3. Building AD From Scratch

### 3.1 Prerequisites checklist

- [ ] Static IP on the future DC
- [ ] DNS pointed **at itself first** (not upstream) — chicken/egg, this is intentional: a DC's own DNS server *is* the thing that will host the SRV records clients need, so the DC must trust itself as authoritative before anyone else can be told where to look
- [ ] NTP source reachable (PDC Emulator will become authoritative time source for the domain — see §1.2)
- [ ] Server OS ≥ Windows Server 2016 for modern functional levels
- [ ] Decide **forest/domain functional level** up front — raising it later is one-way (it gates which Kerberos encryption types, replication features, and trust capabilities are available)

### 3.2 Install & promote

```powershell
# 1. Install the role
Install-WindowsFeature AD-Domain-Services -IncludeManagementTools

# 2. Promote to first DC in a new forest
Install-ADDSForest `
  -DomainName "hpc.internal" `
  -DomainNetbiosName "HPC" `
  -InstallDns:$true `
  -ForestMode "WinThreshold" `
  -DomainMode "WinThreshold" `
  -SafeModeAdministratorPassword (ConvertTo-SecureString "DSRM-P@ss" -AsPlainText -Force)
```

> 💡 **DSRM password** is separate from the domain admin password — it's the *local* recovery-mode credential for that one DC, used to boot into Directory Services Restore Mode if the NTDS.dit database itself is corrupted. Write it down; it's not stored anywhere retrievable.

### 3.3 What just happened internally

1. NTDS.dit created at `%SystemRoot%\NTDS`
2. SYSVOL share created, seeded with default GPOs (`Default Domain Policy`, `Default Domain Controllers Policy`)
3. DNS zone `hpc.internal` created, auto-populated with **SRV records** — this is the part Linux clients will query:

```bash
# Verify SRV records exist — this is how any client (Linux or Windows) discovers a DC
dig SRV _ldap._tcp.hpc.internal
dig SRV _kerberos._tcp.hpc.internal
```

If those return nothing, **nothing downstream will ever work** — fix DNS before touching a single Linux box.

### 3.4 Verification pass (do this before declaring victory)

```powershell
dcdiag /v                     # full DC health check
repadmin /replsummary         # replication health (matters once you add DC #2)
Get-ADDomainController -Filter *   # confirm DC is registered
```

```bash
# From any machine, confirm Kerberos realm is answering
nc -zv dc01.hpc.internal 88
nc -zv dc01.hpc.internal 389
```

---

## 4. Integrating Linux / HPC Nodes

This is the part most guides get wrong by using `winbind` (NTLM-era, built for Samba file-server interop, deprecated for pure Kerberos joins) or raw `pam_ldap` + `nss_ldap` (works, but reinvents caching, TTL, and offline auth badly — see §2.4). **Use SSSD.** It's the modern standard and is what `realmd` configures for you automatically.

### 4.1 Join a compute node to the domain

```bash
# 1. Discover the domain (validates DNS + Kerberos reachability — same SRV records as §3.4)
realm discover hpc.internal

# 2. Join (creates a computer object + keytab automatically)
realm join --user=ahmed hpc.internal

# 3. Confirm
realm list
```

`realm join` under the hood:
1. `kinit` as `ahmed` to get a TGT (this is why you need a *human* AD account with join permission — the join itself is authenticated Kerberos, not anonymous)
2. Creates a **computer object** in AD (`CN=gpu209-06,CN=Computers,DC=hpc,DC=internal`) — the machine itself becomes a first-class Kerberos principal, e.g. `gpu209-06$@HPC.INTERNAL`
3. Generates a **machine keytab** at `/etc/krb5.keytab` — a file containing the node's *own* long-term Kerberos key, used so the node itself can authenticate services (like `sshd` with GSSAPI, or NFS with Kerberos sec) without a human typing a password
4. Writes `/etc/sssd/sssd.conf`, wiring NSS and PAM to point at SSSD as covered in §2.4

### 4.2 Minimal `sssd.conf` for an HPC compute node (RFC2307 / POSIX attributes)

```ini
[sssd]
domains = hpc.internal
services = nss, pam

[domain/hpc.internal]
id_provider = ad
auth_provider = ad
access_provider = ad

# Critical for HPC: consistent numeric UID/GID across every node.
# Without this, SSSD auto-generates UIDs per-node → NFS/Weka permission chaos.
ldap_id_mapping = False
ldap_user_uid_number = uidNumber
ldap_user_gid_number = gidNumber

cache_credentials = True        # offline login survives a DC outage
enumerate = False               # don't bulk-cache every domain user — scale killer at HPC size
```

> ⚠️ **`ldap_id_mapping = False` requires the AD schema to actually carry `uidNumber`/`gidNumber` (RFC2307).**
> This is a legacy extension originally called "Identity Management for Unix," an add-on Microsoft shipped specifically so AD could interoperate with Unix/Linux NSS — it is *not* present by default in a fresh AD forest and must be deliberately schema-extended and populated per user.
> If your forest was never extended this way, set `ldap_id_mapping = True` and let SSSD algorithmically derive UIDs from the object's SID — but then **every node must use the same SSSD ID-mapping algorithm/range**, or a user gets a *different* UID on different nodes → broken shared-filesystem ownership. This is the #1 cause of "my job's output files are owned by nobody" on AD-joined clusters.

### 4.3 Slurm-specific note

Slurm itself doesn't authenticate users — PAM/NSS does, before Slurm ever sees the job (§2 covers exactly how). What Slurm *does* care about:
- `slurmd` calls the equivalent of `getpwnam()` under the hood → must resolve identically on every node (→ back to §4.2's UID consistency requirement)
- `MungeAuth` is independent of AD entirely — don't conflate the two. AD/SSSD gives you *who the user is* (identity + login authorization); Munge gives you *inter-node trust for Slurm's own RPC traffic between daemons*. They solve completely different problems and neither depends on the other.
- If you gate cluster access via AD group membership, use `access_provider = simple` in SSSD with `simple_allow_groups = hpc-users`, not a Slurm-side ACL — keep the trust boundary at the OS layer, so `ssh` itself already refuses non-members before Slurm is ever involved.

### 4.4 Verification pass

```bash
realm list                              # confirms join + config source
getent passwd ahmed                     # NSS resolution working? (§2.2)
id ahmed                                # UID/GID as expected, matches other nodes?
kinit ahmed && klist                    # can this node get a TGT? (§1.1)
sudo systemctl status sssd              # daemon healthy?
sssctl user-checks ahmed                # SSSD's own built-in diagnostic — very underused
```

---

## 5. Knowledge Prerequisites (the stuff that isn't optional)

| Concept | Why you can't skip it |
|---|---|
| **DNS SRV records** | AD *is* a DNS-based service locator (§0.4). No SRV records = no domain discovery, full stop. |
| **NTP / time sync** | Kerberos tickets are timestamped; >5 min skew = silent auth failures with misleading errors (§1.1). |
| **LDAP DN syntax** | `CN=`, `OU=`, `DC=` — every object address, every filter, every ACL references this; inherited straight from X.500 (§0.1–0.2). |
| **RFC2307 schema** | The bridge between Windows SIDs and POSIX uid/gid — decide your ID-mapping strategy *before* joining 200 nodes, not after (§4.2). |
| **PAM vs. NSS separation** | "Login doesn't work" is meaningless until you know whether identity resolution or authentication is failing (§2). |
| **Kerberos realms vs. NetBIOS domains** | Realm names are UPPERCASE by convention (`HPC.INTERNAL`), domain names are not — mixing these up breaks keytabs silently. |
| **Site & Subnet topology** | Tells clients which DC is "local" — matters a lot once you have DCs in >1 datacenter/region; a misconfigured site makes every login round-trip to a far-away DC. |

---

## 6. Common Failures & Debug Playbook

### 6.1 Symptom → Cause → Command matrix

| Symptom | Likely Cause | Diagnose With |
|---|---|---|
| `kinit: Clock skew too great` | NTP drift between node and DC | `chronyc tracking` / `ntpdate -q dc01.hpc.internal` |
| `realm discover` returns nothing | DNS not pointing at a DC, or SRV records missing | `dig SRV _kerberos._tcp.<realm>` |
| `id user` → `no such user` | SSSD not caching, or `access_provider` denying, or a *local* `files` entry shadowing it (§2.2) | `sudo sssctl user-checks <user>`, check `/var/log/sssd/sssd_<domain>.log`, check `/etc/passwd` for a colliding local entry |
| Login works, but wrong UID on this node vs. another | Inconsistent ID-mapping config across nodes | Diff `sssd.conf` across nodes; check `ldap_id_mapping` setting matches (§4.2) |
| `kinit` works, `ssh` still fails | NSS is fine but PAM's `auth`/`account` stack is misordered, or GSSAPI not enabled in sshd (§2.3) | `sshd -T \| grep -i gssapi`; check `/etc/pam.d/sshd` includes `pam_sss.so` in the right position |
| Node joined, then falls off domain after weeks | Machine account password rotation missed (default 30-day AD computer password change, tied to the machine's own Kerberos principal from §4.1) | `sudo net ads testjoin` (or `realm list` for staleness); check `adcli`/SSSD renewal timer/cron |
| DC replication errors | Network partition, or lingering objects after a DC was force-demoted | `repadmin /replsummary`, `repadmin /showrepl` on the DC |
| Group membership not applying | **Token bloat / nested-group depth**, or Kerberos ticket cached before group change | User must `kdestroy && kinit` — group membership is baked into the ticket at issue time (§1.1), not re-checked live |

### 6.2 The "it's always DNS" corollary

If nothing else in this doc helps: 90% of AD-Linux integration failures trace back to one of:
1. Node's `/etc/resolv.conf` not pointing at an AD-integrated DNS server
2. Reverse DNS (PTR record) missing for the node — Kerberos SPN validation can depend on it
3. Time not synced

Check all three **before** diving into SSSD log verbosity.

### 6.3 Turning up log verbosity when stuck

```ini
# /etc/sssd/sssd.conf
[domain/hpc.internal]
debug_level = 9
```
```bash
sudo systemctl restart sssd
sudo tail -f /var/log/sssd/sssd_hpc.internal.log
```

On the DC side:
```powershell
# Enable Kerberos event logging for the failing auth attempt
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa\Kerberos\Parameters" -Name LogLevel -Value 1
# Then check Event Viewer → System log, source "Kerberos"
```

---

## 7. Verification Summary (run this whole block after any change)

```bash
# --- DNS / discovery (§0.4, §3.3) ---
dig SRV _ldap._tcp.hpc.internal +short
dig SRV _kerberos._tcp.hpc.internal +short

# --- Time (§1.1) ---
chronyc tracking | grep "System time"

# --- Kerberos (§1.1) ---
kinit ahmed && klist

# --- NSS/PAM/SSSD (§2, §4) ---
getent passwd ahmed
id ahmed
sssctl user-checks ahmed
systemctl is-active sssd

# --- Cross-node consistency (run on 2+ nodes, diff output) ---
id ahmed
```

```powershell
# --- DC health ---
dcdiag /v
repadmin /replsummary
netdom query fsmo
```

> ✅ If every command above returns clean output and UIDs match across nodes, the integration is sound end-to-end: DNS discovery → Kerberos ticket → NSS resolution → PAM authorization → consistent POSIX identity.