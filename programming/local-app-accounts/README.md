---
sidebar_group: Local App Accounts
---

# Local App Accounts: Six Tea Talks on Teaching an App Who Is Who

> A six-part series on adding accounts to a desktop app that used to trust everyone at the keyboard. By the end you'll know what accounts should promise, how to handle passwords and sessions, and where this kind of design tends to go wrong.

Two people share one laptop and one desktop app. Ahmed runs training jobs, Abdelrahman babysits the storage, and until now the app showed them the same clusters, the same notes and the same saved passwords. This series follows how that app learns to tell them apart, one locked door at a time.

Each talk is short enough to finish before the tea goes cold, and each stands on its own. Read them in order, or jump to the one you need.

## The route

| # | Page | The question it answers |
|---|------|-------------------------|
| 1 | [Threat Model and First Launch](/programming/local-app-accounts/threat-model-and-first-launch.md) | What should accounts promise, and what should they not? |
| 2 | [Sign-In Hygiene](/programming/local-app-accounts/sign-in-hygiene.md) | How do you store and check passwords without leaking hints? |
| 3 | [Sessions and Two Walls](/programming/local-app-accounts/sessions-and-two-walls.md) | Who's signed in, and who may see which data? |
| 4 | [Old Data and Background Work](/programming/local-app-accounts/old-data-and-background-work.md) | What happens to data and monitors that existed before accounts? |
| 5 | [Lock, Recovery and Going Online](/programming/local-app-accounts/lock-recovery-and-going-online.md) | What about the lock screen, forgotten passwords and online sign-in? |
| 6 | [Reviewing the Design](/programming/local-app-accounts/reviewing-the-design.md) | Where should you push back, and what should you read next? |

## Who this is for

Developers adding sign-in to a local desktop app, or reviewing someone else's design for it.

## Contents

| File | Description |
| --- | --- |
| [Threat Model and First Launch](/programming/local-app-accounts/threat-model-and-first-launch.md) | What accounts should promise (and what they shouldn't), plus the very first sign-up |
| [Sign-In Hygiene](/programming/local-app-accounts/sign-in-hygiene.md) | Password hashing, decoy checks, identical errors and throttling |
| [Sessions and Two Walls](/programming/local-app-accounts/sessions-and-two-walls.md) | Who's signed in, "keep me signed in", and authorization at the door and at the data |
| [Old Data and Background Work](/programming/local-app-accounts/old-data-and-background-work.md) | Claiming pre-existing data safely, and tying monitors to the signed-in person |
| [Lock, Recovery and Going Online](/programming/local-app-accounts/lock-recovery-and-going-online.md) | The lock screen, forgotten passwords, and the door left open for online sign-in |
| [Reviewing the Design](/programming/local-app-accounts/reviewing-the-design.md) | Where to push back, common mistakes, book chapters to read, and exercises |

## The source

The series is built from a design write-up of a real desktop app, which says it was tried by hand on Linux and macOS. Claims about how that app behaves come from the write-up and have not been independently verified. Security guidance is checked against OWASP's cheat sheets, and the book chapters suggested for further reading are the author's own mapping.