
# The Munge Key in Git: Secrets, Vault and Rotation

<!-- related-block -->
<div class="reading-time">9 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [The GPU Node That Thought It Had 1000 MB: Roles and Variables](/fields/devops/ansible/roles-and-variables.md)  ·  **See also:** [Ansible Cheatsheet: Every Step from the Series](/fields/devops/ansible/cheatsheet.md)

</div>


> **Part 6 of the [Ansible series](/fields/devops/ansible/README.md).** [Part 5](/fields/devops/ansible/rolling-maintenance.md) changed busy nodes safely. This last page handles the secrets those playbooks need: encrypt them in the repo, replace one that leaked, roll the new one out without breaking the cluster, and keep secrets out of logs.

- [The Munge Key in Git: Secrets, Vault and Rotation](#the-munge-key-in-git-secrets-vault-and-rotation)
  - [Found in a fork](#found-in-a-fork)
  - [Why this key matters](#why-this-key-matters)
  - [Vault in five minutes](#vault-in-five-minutes)
  - [Encrypting isn't enough: history](#encrypting-isnt-enough-history)
  - [Rotating without splitting the cluster](#rotating-without-splitting-the-cluster)
  - [What ansible-core 2.22 hides, and what it doesn't](#what-ansible-core-222-hides-and-what-it-doesnt)
  - [When the password is missing or wrong](#when-the-password-is-missing-or-wrong)
  - [A guard that stops the next one](#a-guard-that-stops-the-next-one)
  - [Back to the fork](#back-to-the-fork)
  - [References](#references)

---

## Found in a fork

Two years ago someone added the `munge` role to the playbook repo. The key went in where every other file goes: `roles/munge/files/munge.key`, in plain bytes. Since then the repo has been cloned by four admins, a contractor, and a CI runner, and mirrored to a second Git server "for backup".

Today a security review finds it. Somebody says "let's just encrypt it with vault", runs one command, commits, and calls it done.

It isn't done. Every clone, every mirror, and every old commit still has the original key. This page does the whole job.

> [!NOTE]
> Lab: ansible-core **2.22.0** (and 2.21.6 for one comparison), munge **0.5.15**, Slurm 23.11.4 on six Ubuntu 24.04 nodes. The passwords on this page are fakes made for the lab.

---

## Why this key matters

**munge** is how Slurm daemons and commands prove who they are to each other. Every host has the same key; a credential made with it says "this is uid 1000 on head01", and anyone with the key is believed. With the cluster's munge key you can mint credentials that the cluster accepts. The `mungekey` man page puts it simply: every munged in a security realm must use the same key, created on one host and copied securely to the others.

So a leaked munge key means two jobs: stop storing secrets in plain text, **and** replace the key that leaked.

---

## Vault in five minutes

**ansible-vault** encrypts files (or single values) with a password, using AES-256. Ansible decrypts them in memory when a playbook needs them, so the repo only ever holds ciphertext.

1. Keep the vault password **outside** the repo, readable only by you:

```bash
mkdir -p ~/.config/cluster-ansible
openssl rand -base64 32 > ~/.config/cluster-ansible/vault-pass
chmod 600 ~/.config/cluster-ansible/vault-pass
```

Share it with the other admins the way you share any admin password (a password manager), never through the repo.

2. Tell Ansible where it is, in `ansible.cfg` under `[defaults]`:

```ini
vault_password_file = ~/.config/cluster-ansible/vault-pass
```

3. Put secret variables in their own **fully encrypted** file. Here, the password the Slurm accounting daemon would use, for the `head` group. A `group_vars` entry can be a folder instead of a file, so plain and secret variables sit side by side:

```bash
mkdir -p inventory/group_vars/head
printf 'slurmdbd_storage_pass: "Tr0ub4dor&3-not-real"\n' > inventory/group_vars/head/vault.yml
ansible-vault encrypt inventory/group_vars/head/vault.yml
head -1 inventory/group_vars/head/vault.yml
```

```text
$ANSIBLE_VAULT;1.1;AES256
```

Day to day you use `ansible-vault view` and `ansible-vault edit` on that file, and never decrypt it to disk.

> [!TIP]
> You can also encrypt single values inside a plain YAML file (`ansible-vault encrypt_string`). It works, but then a file named `vault.yml` is half plain text, and a simple "is this file encrypted?" check can't tell. We use whole-file encryption so the guard [at the end](#a-guard-that-stops-the-next-one) stays simple. Our guard flagged the inline style the first time we ran it.

---

## Encrypting isn't enough: history

Back to the key. Encrypting the file in place hides the *current* version. Git keeps every old one. In the lab we committed a plain key, then later replaced it with an encrypted file, then asked Git for the old commit:

```bash
git show 0508587:roles/munge/files/munge.key | md5sum
```

```text
b628443e71788bad8853dad92a8caa0b  -
```

Byte for byte, the leaked key. Rewriting history doesn't fix it either: the clones and the mirror still have it.

So the only real fix is a **new key**, made fresh, never committed in plain text:

```bash
dd if=/dev/urandom of=roles/munge/files/munge.key bs=1024 count=1
ansible-vault encrypt roles/munge/files/munge.key
```

That's 1024 random bytes, 8192 bits, the top of the 256–8192-bit range `mungekey(8)` accepts. `mungekey` itself can create the key too, but it writes to the munge directory on the host you run it on; for a repo, `dd` is simpler.

The `copy` module decrypts a vault-encrypted `src` file automatically when it deploys it. The role (`roles/munge/tasks/main.yml`) doesn't mention vault at all:

```yaml
- name: Install the cluster's munge key
  ansible.builtin.copy:
    src: munge.key
    dest: /etc/munge/munge.key
    owner: munge
    group: munge
    mode: "0400"
  notify: Restart munge
```

and `roles/munge/handlers/main.yml`:

```yaml
- name: Restart munge
  ansible.builtin.systemd_service:
    name: munge
    state: restarted
```

---

## Rotating without splitting the cluster

Here's the trap. Every host must have the **same** key at the same time. Part 5 taught you to change nodes a few at a time; do that here and you split the cluster in two.

We showed it in the lab by deploying the new key to cn001 only. A credential made on head01 (old key) was rejected by cn001 and accepted by cn002:

```bash
docker exec head01 munge -n > /tmp/cred     # in the lab; on a real cluster: ssh head01 munge -n
```

```text
cn001: unmunge: Error: Invalid credential
cn002: STATUS:          Success (0)
```

A minute later the controller had marked cn001 as not responding (`idle*` in `sinfo`), and logged `Zero Bytes were transmitted or received` talking to it.

So the playbook (`playbooks/munge.yml`) targets every host in one go, with no `serial`:

```yaml
- name: One munge key for the whole cluster, all hosts at once
  hosts: head:nodes
  become: true
  force_handlers: true
  roles:
    - munge
```

```bash
ansible-playbook playbooks/munge.yml
```

Every host that didn't have the new key yet reported `changed=2` (the file and the restart); cn001, which already had it, reported `changed=0`. Then:

| Check | Result in the lab |
| --- | --- |
| A credential from head01, decoded on cn001, cn004, gpu001 | `Success (0)` on all three |
| cn001 in `sinfo` | Back to `idle` on its own, about 75 seconds later (the controller's next check) |
| A batch job sent to cn001 | `Started JobId=6 in batch on cn001`, exit status 0 |
| Run the playbook again | `changed=0` on all six hosts |

Restarting munged was enough. We didn't restart slurmd or slurmctld; the Slurm daemons ask munged for every credential.

> [!CAUTION]
> We rotated with no jobs running. While hosts disagree about the key (between the first and last host's restart), any Slurm traffic between them fails, including job launches. Do it in a quiet window, or drain the partition first and resume it afterwards. Never with `serial`.

---

## What ansible-core 2.22 hides, and what it doesn't

The classic second leak: you run with `--diff` or `-v` to see what changed, and the secret is right there in the output, in your terminal and in your CI logs. **ansible-core 2.22 changed this.** Its changelog: Ansible now automatically redacts known secret values from its output, including the plaintext of vault-encrypted values and every value in a vault-encrypted variables file, replacing them with `$REDACTED$`. Masking only affects output; tasks still get the real value.

We tested where it holds and where it stops, with the same vault and the same play on 2.22.0 and 2.21.6:

| What's printed | ansible-core 2.21.6 | ansible-core 2.22.0 |
| --- | --- | --- |
| The secret itself (`debug`) | `Tr0ub4dor&3-not-real` | `$REDACTED$` |
| The secret inside command output (`grep StoragePass` on the deployed file) | `StoragePass=Tr0ub4dor&3-not-real` | `StoragePass=$REDACTED$` |
| `--diff` of a file containing the secret | `+StoragePass=Tr0ub4dor&3-not-real` | `+StoragePass=$REDACTED$` |
| A value **derived** from the secret (`\| b64encode`) | `VHIwdWI0ZG9yJjMtbm90LXJlYWw=` | `VHIwdWI0ZG9yJjMtbm90LXJlYWw=` |

That last row is the gap: masking matches the exact secret strings it knows about. Transform the secret (encode it, hash it, build a connection string from parts), and the result isn't recognized. Decode that base64 and you have the password. The deployed file itself still has the real password, of course; masking is about output only.

So for any task that handles a secret in a way you're not sure masking catches, and for anyone still on 2.21 or older, keep the old defence:

```yaml
    - name: A value derived from the secret, hidden
      ansible.builtin.debug:
        msg: "b64={{ slurmdbd_storage_pass | b64encode }}"
      no_log: true
```

With `no_log: true`, the task's output was hidden completely on 2.22. Add `diff: false` to template or copy tasks that write secrets, so `--diff` doesn't show their content on older versions.

Rule of thumb: **masking is a seatbelt, not a reason to drive faster.** Keep `no_log` on tasks that touch secrets.

---

## When the password is missing or wrong

Both failures are clear and stop the run before anything changes. We ran the munge playbook with a config that had no `vault_password_file`:

```text
[ERROR]: Task failed: A vault password or secret must be specified to decrypt /root/cluster-ansible/roles/munge/files/munge.key
```

And with only a wrong password:

```text
[ERROR]: Task failed: Decryption failed (no vault secrets were found that could decrypt).
```

Both exited 2. One thing that surprised us while testing: passing `--vault-password-file` with a wrong password *as well as* the right one in `ansible.cfg` worked fine. Ansible tries every password it has, so to test "wrong password", remove the right one.

---

## A guard that stops the next one

The leak happened because nothing stopped a plain key from being committed. This script fails if any file that should be secret isn't vault-encrypted. Save as `tools/check-secrets.sh`:

```bash
#!/usr/bin/env bash
# Fail if any file that should hold a secret is not vault-encrypted.
# Secret files: anything named *.key or vault.yml under roles/ or inventory/.
set -uo pipefail
fail=0
while IFS= read -r -d '' f; do
  if ! head -c 14 "$f" | grep -q '^\$ANSIBLE_VAULT'; then
    echo "NOT ENCRYPTED: $f"; fail=1
  fi
done < <(find roles inventory -type f \( -name '*.key' -o -name 'vault.yml' \) -print0)
[ $fail -eq 0 ] && echo "secrets check: ok"
exit $fail
```

Run against the repo before the fix, it caught both problems and exited 1:

```text
NOT ENCRYPTED: roles/munge/files/munge.key
NOT ENCRYPTED: inventory/group_vars/head/vault.yml
```

(The second was the inline `encrypt_string` style from the tip above.) After the fix: `secrets check: ok`, exit 0.

Make Git run it before every commit:

```bash
chmod +x tools/check-secrets.sh
ln -sf ../../tools/check-secrets.sh .git/hooks/pre-commit
```

We tested it by adding a plain `test.key`: `git commit` printed `NOT ENCRYPTED: roles/munge/files/test.key`, exited 1, and no commit was made. A Git hook lives in each clone and isn't shared, so also run the script in CI, where nobody can skip it.

---

## Back to the fork

The security review finds the key, and this time the team does the whole job. They generate a new key and encrypt it before it's ever committed. The playbook rolls it to every host in one go during a quiet hour, credentials verify everywhere, and the one node that briefly showed `idle*` comes back by itself. The old key, still sitting in every clone and in the mirror, now opens nothing.

The slurmdbd password moves into an encrypted `vault.yml`. The pipeline that prints `--diff` shows `$REDACTED$` on 2.22, and the tasks that transform secrets carry `no_log`. And the next person who drops a plain key into `roles/` gets a red `NOT ENCRYPTED` from their own commit and from CI, before it ever reaches a fork.

**Takeaway:** encrypt secrets with vault before the first commit, rotate anything that was ever committed in plain text, roll shared keys to every host at once, and keep `no_log` even though 2.22 masks most secrets.

**Next:** [Part 7, the cheatsheet](/fields/devops/ansible/cheatsheet.md), has every step from the series as copy-paste commands.

**Back to:** [the Ansible series index](/fields/devops/ansible/README.md). From here, the [Node Health Check](/fields/system-administration/node-health-check/README.md) pages are a natural thing to deploy and run with these roles.

---

## References

- [Protecting sensitive data with Ansible vault](https://docs.ansible.com/projects/ansible/latest/vault_guide/index.html): encrypting files and variables, password files, `view` and `edit`.
- [Ansible vault: managing passwords](https://docs.ansible.com/projects/ansible/latest/vault_guide/vault_managing_passwords.html): `vault_password_file` and multiple vault passwords.
- [ansible-core 2.22 changelog](https://github.com/ansible/ansible/blob/stable-2.22/changelogs/CHANGELOG-v2.22.rst): secret masking, what is registered as a secret, and `$REDACTED$`.
- [Logging Ansible output](https://docs.ansible.com/projects/ansible/latest/reference_appendices/logging.html): `no_log` and what reaches logs.
- [ansible.builtin.copy](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/copy_module.html): `decrypt` (default true) for vault-encrypted `src` files.
- [mungekey(8) (Ubuntu 24.04)](https://manpages.ubuntu.com/manpages/noble/man8/mungekey.8.html): every munged in a realm uses the same key, key size range.
- [Slurm: Authentication plugins](https://slurm.schedmd.com/authentication.html): how Slurm uses munge.
- [githooks(5)](https://git-scm.com/docs/githooks#_pre_commit): the `pre-commit` hook.