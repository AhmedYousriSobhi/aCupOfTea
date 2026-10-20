---
id: sessions-and-two-walls
sidebar_label: Sessions and Two Walls
summary: How an app remembers who is signed in, why remember-me stores a fingerprint instead of a token, and why authorization needs one check at the door and another at the data.
level: intermediate
type: [concept, guide]
domains: [software-engineering, system-design]
tags: [programming, system-design, software-engineering]
relations:
  prerequisites: [sign-in-hygiene]
---

# Who's Home, and What May They Touch? Sessions and Two Walls

*Local App Accounts, tea talk 3 of 6. Previous: [Sign-In Hygiene](/programming/local-app-accounts/sign-in-hygiene.md). Next: [Old Data and Background Work](/programming/local-app-accounts/old-data-and-background-work.md).*

The password was right, and the app now knows Ahmed is home. This talk covers what "home" means in memory, how the app can remember him tomorrow without storing his password, and the part that actually keeps Abdelrahman out of Ahmed's clusters.

---

## The one-sentence version

**Authorize at the door and again at the data, and make the build fail when someone forgets the door.**

---

## Words you'll meet

| Term | Plain meaning |
| --- | --- |
| **Session** | The app's memory of "this person is signed in right now" |
| **Token** | A random secret that stands in for a password after sign-in |
| **Fingerprint** | A hash of the token, stored instead of the token itself |
| **Keychain** | The operating system's protected store for secrets, tied to the *computer* user |
| **Main process / UI process** | In many desktop apps: the part that does privileged work, and the part that draws the window. The UI process is treated as less trusted |
| **IDOR** | *Insecure direct object reference*: a request names a resource ("cluster 42") and the app serves it without checking that the asker owns it |
| **Deny by default** | If no rule explicitly allows a request, it is refused |

---

## The Memory

Once the password is right, the main process notes that Ahmed is home. That note lives in memory in the app's main process. Not a cookie, not a file. The screen is told his name and nothing else.

The note can **announce changes**, and three things listen:

1. The Cartographer, who redraws the map of what's visible
2. The Curtain, which lifts (a new sign-in never starts locked)
3. The app itself, which starts or stops all its background work (talk 4)

### "Keep me signed in on this computer"

If Ahmed ticks the box, the app does *not* remember his password. It makes a **random token**, seals it with the computer's keychain, and stores only a **fingerprint** of that token beside his account. On the next launch it unseals the token, fingerprints it and compares. If anything is off (keychain unavailable, token revoked, account gone), you simply get the sign-in screen.

- **One slot per computer.** Remembering Abdelrahman replaces Ahmed.
- **Sign-out or reset deletes the fingerprint**, revoking the token at once.
- **Changing the password revokes the old token**, and if the box was ticked, a fresh one is sealed so Ahmed stays signed in.
- **No keychain, no promise.** Where there isn't a usable keychain, the box is switched off and says why, instead of promising something it can't deliver.

Why a fingerprint? If someone copies the database, a stored fingerprint can verify a token but can't be turned back into one. Storing the token itself would hand over a working key.

---

## Wall one: the Bouncer

Everything the screen asks of the engine goes past the Bouncer, who asks two questions:

1. *Did this come from the app's own page?*
2. *Is this person allowed to ask this?* With nobody signed in, refuse everything except a short list of public doors (the sign-in screens and the window's own buttons).

He also carries a list of what each request is **about**. If a request says "edit cluster 42," he checks that cluster 42 belongs to a profile the signed-in person owns. Abdelrahman asking for Ahmed's cluster gets *exactly* the same answer as asking for one that doesn't exist.

And here's the detail worth stealing: the build has a check that **fails** if anyone adds a request that names a cluster, profile, note or rule and forgets to put it on the Bouncer's list. The easiest mistake in this design is also the one the tooling refuses to let through.

---

## Wall two: the Cartographer

Checking at the door is good; checking at the shelves is better. Every question the app asks the database about profiles, clusters, notifications, reminders or watches passes through one ownership rule. A feature that forgets to filter *cannot*, because the filter is part of how the database answers.

The map, short enough to memorise:

| Situation | What you see |
| --- | --- |
| No accounts exist yet | Everything, as it always was (so upgrades behave) |
| Accounts exist, nobody signed in | Nothing |
| Signed in as Ahmed | Ahmed's profiles, and through them his clusters, notes and so on |
| A profile nobody owns | Nothing, for anybody, and nothing runs for it |

Ownership is a single label, the **owner**, on each profile. Clusters, notes and the rest belong to a profile or a cluster, so they inherit it. Anything new that gets stored must say how it reaches an owner.

### One click, both walls

Abdelrahman clicks *Edit* on a cluster. The Bouncer checks the request is from the app's page and that this cluster is one of *his*. If not, it's refused like "no such cluster." If it passes, the database applies the ownership rule *again*. A mistake in one wall isn't an open door.

---

## What the references recommend

IDOR sits under OWASP's top-ranked web risk, Broken Access Control. OWASP's Authorization Cheat Sheet says to **deny by default**, to **validate permissions on every request** (checking most of them is not enough), and to write tests proving the permissions work. Its Developer Guide checklist adds: send all requests through access checks unless they're public, and use a **single component** to make authorization decisions. The Bouncer is that single component, and the build check is the test.

> **Lesson.** Authorize at the door and again at the data. Make "no access" and "doesn't exist" the same answer, so refusals don't leak what exists. Store a fingerprint of the token, never the token.

---

## Recap

- The session lives in the main process's memory, and announces changes to whoever cares.
- "Keep me signed in" stores a fingerprint of a random, keychain-sealed token, with one slot per computer.
- Two walls: a request-level check with a build guard, and an ownership rule inside the database.

**Next tea talk:** [Old Data and Background Work](/programming/local-app-accounts/old-data-and-background-work.md), where a year of pre-account data finds its owner and two nasty bugs teach a lesson.

---

## References

- OWASP Cheat Sheet Series, [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html): deny by default, validate permissions on every request, test the permissions
- [OWASP Developer Guide, Enforce Access Controls checklist](https://devguide.owasp.org/en/04-design/02-web-app-checklist/07-access-controls/): route requests through access checks, use a single component for authorization decisions
- [OWASP Top 10, A01 Broken Access Control](https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/): where IDOR sits