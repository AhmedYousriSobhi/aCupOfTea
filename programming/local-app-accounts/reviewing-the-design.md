---
id: reviewing-the-design
sidebar_label: Reviewing the Design
summary: Six review questions the design leaves open, a table of mistakes it avoids, the Designing Data-Intensive Applications chapters that explain why, and six exercises.
level: intermediate
type: [concept, guide]
domains: [software-engineering, system-design]
tags: [system-design, software, programming]
---

# Reviewing the Design: Where Would You Push Back?

*Local App Accounts, tea talk 6 of 6. Previous: [Lock, Recovery and Going Online](/programming/local-app-accounts/lock-recovery-and-going-online.md).*

A good design is not one with no open questions. It is one where the open questions are written down. This last talk puts the design on the review table: six questions it leaves open, the common mistakes it avoids, the book chapters that explain *why* it works, and a few exercises so the ideas stick.

---

## The one-sentence version

**Every design makes implicit promises, and reviewing is the skill of spotting them and deciding which ones you'd write down.**

---

## Six questions to push back on

Think about each before reading on. There are no single right answers.

1. **Remember-me on a shared login.** The token is sealed by a keychain that belongs to the *computer* user. So when Abdelrahman opens the app from the same computer login, whose account does he land in? Should the checkbox say so?
2. **Claiming old data.** If any account can claim any unowned profile, could a second account created during the migration window take the first person's data without ever seeing the names? Who should be allowed to claim?
3. **The locked state.** The screen is covered, but does the engine also *refuse* requests while locked? A covered page and a refusing engine are different guarantees.
4. **Shared settings that leak.** If the known-SSH-hosts list is shared between accounts, can it reveal hostnames that the pre-claim hiding was meant to protect?
5. **The backup copy.** The claim flow writes a safety copy of the very data you're protecting. Where does it live, with what file permissions, and when is it deleted?
6. **Hash cost.** Given the stated trade-off, what would you raise the scrypt settings to, and what would it do to sign-in time on a slow laptop?

---

## Mistakes this design avoids

| Common mistake | What the design does instead |
| --- | --- |
| Overpromising ("secure accounts!") | States the threat model, including what it doesn't do |
| Different errors for "no such user" and "wrong password" | One message, one look, same timing via a decoy |
| Storing a "remember me" password or a raw token | Stores a fingerprint of a random token |
| Authorization only in the UI | Checks at the door *and* at the data |
| Forgetting to guard a new endpoint | The build fails until it's on the list |
| Background tasks outliving the session | Stops them all, then clears their cached readings |
| Silent data migration | Explicit consent, backup, atomic change |
| Treating lock like sign-out | Two separate states with different effects |
| Recovery that leaks secrets | Recovery wipes them |

---

## Go deeper: *Designing Data-Intensive Applications*

Martin Kleppmann's *Designing Data-Intensive Applications* (O'Reilly, 2017) is about data systems at scale, but several of its chapters explain why the small decisions in this series are right. The mapping below is my own reading of how the book's ideas apply, not claims the book makes about this design. Chapter numbers refer to the first edition; if you have a newer edition, check its table of contents, because the numbering may differ.

| Idea in this series | Where to read more | What it teaches |
| --- | --- | --- |
| The self-describing password record, upgraded at the next sign-in | **Ch. 4, Encoding and Evolution** | Backward and forward compatibility: new code must read old records, and formats need room to change |
| The all-or-nothing claim, and "what if someone claimed one in between?" | **Ch. 7, Transactions** | Atomicity, isolation, and preventing lost updates when two writers collide |
| Cached "last readings" going stale, and the change announcement | **Ch. 11, Stream Processing**, and the book's **derived data** theme | Keeping caches and other derived data in step with their source |
| The build check that stops a forgotten guard | **Ch. 1, Reliable, Scalable, and Maintainable Applications** | Human error is a major cause of failures, so design to make mistakes hard |
| What changes when the app goes online | **Chs. 5, 6, 8 and 9** (replication, partitioning, distributed-systems trouble, consistency and consensus) | Everything in this series assumed *one computer*. A shared server brings these problems in |

---

## Try it yourself

1. **Threat model in five lines.** Pick an app you use. Write what accounts would protect against and what they wouldn't, then compare with [talk 1](/programming/local-app-accounts/threat-model-and-first-launch.md).
2. **Self-describing hash.** Implement the record format from [talk 2](/programming/local-app-accounts/sign-in-hygiene.md) in your language, with a function that verifies a password and says whether the record needs upgrading.
3. **Make it identical.** Write a sign-in whose response is the same text, and takes about the same time, for an unknown user and a wrong password. Then measure both.
4. **Break the door guard.** Add an endpoint that takes a resource id, forget the ownership check, and write the test or build step that catches it ([talk 3](/programming/local-app-accounts/sessions-and-two-walls.md)).
5. **Late arrival.** Build a tiny "start all monitors on sign-in" loop, register one monitor *after* sign-in, watch it never start, then fix it ([talk 4](/programming/local-app-accounts/old-data-and-background-work.md)).
6. **Review the review.** Pick two of the six questions above, decide your answers, and write the one sentence each would add to the threat model.

---

## Cheat sheet

- **Who's signed in?** One note in the engine's memory.
- **What may they see?** Profiles they own, and everything under them.
- **Where is it enforced?** At the door (Bouncer) and again in the database (Cartographer).
- **A new request names a resource?** The build fails until it's on the Bouncer's list.
- **What stops on sign-out?** Sessions, tunnels, pop-outs and every monitor, plus their cached readings.
- **What does the lock do?** Covers the window; changes nothing underneath.
- **Forgot the password?** A terminal command resets it and wipes the saved secrets.
- **Going online?** Add a second Clerk.

---

## The one-paragraph takeaway

Adding accounts to a local app is mostly honesty plus plumbing. Be honest about what the feature protects, then do the plumbing so the promise holds everywhere: identical failures at sign-in, two independent walls around data, background work that follows the signed-in person, migrations that never surprise, and a lock that isn't a sign-out. Where the design leaves questions open, write them down.

---

## References

- Martin Kleppmann, *Designing Data-Intensive Applications*, O'Reilly, 2017: chapters on encoding and evolution, transactions, stream processing and derived data
- OWASP Cheat Sheet Series, [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- OWASP Cheat Sheet Series, [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- OWASP Cheat Sheet Series, [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [OWASP Developer Guide, Enforce Access Controls checklist](https://devguide.owasp.org/en/04-design/02-web-app-checklist/07-access-controls/)
- [OWASP Top 10, A01 Broken Access Control](https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/)

The "Where would you push back?" questions, the DDIA mapping and the lessons are reviewer commentary, not part of the original design.