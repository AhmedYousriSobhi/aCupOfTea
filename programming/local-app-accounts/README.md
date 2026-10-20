---
sidebar_group: Local App Accounts
---

# Local App Accounts: Six Tea Talks on Teaching an App Who Is Who

Two people share one laptop and one desktop app. Ahmed runs training jobs, Abdelrahman babysits the storage, and until now the app showed them the same clusters, the same notes and the same saved passwords. This series follows how that app learns to tell them apart, one locked door at a time.

Each talk is short enough to finish before the tea goes cold, and each stands on its own. Read them in order, or jump to the one you need.

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