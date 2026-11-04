
# The Curtain, the Locksmith and the Door Already Built

<!-- related-block -->
<div class="reading-time">4 min read</div>


*Local App Accounts, tea talk 5 of 6. Previous: [Old Data and Background Work](/programming/local-app-accounts/old-data-and-background-work.md). Next: [Reviewing the Design](/programming/local-app-accounts/reviewing-the-design.md).*

Three things are left to design, and each one is where good intentions usually leak: what happens when someone walks away, what happens when someone forgets their password, and what happens when the app one day needs a real sign-in service.

---

## The one-sentence version

**A lock protects the screen while work continues, a recovery path must destroy the thing worth stealing, and the rest of the app should depend on a *role*, not on any one way of signing in.**

---

## The Curtain (lock screen)

**Scene.** Ahmed goes to get tea. The window locks.

This is **not** a sign-out: terminals keep running, jobs keep being watched, reminders still fire. A curtain is drawn over the window and the app underneath is made inert, so Tab can't wander into it.

It falls three ways:

- **By hand:** a keyboard shortcut, or the account menu.
- **When idle:** after a stretch with no activity in the app's *own* windows. The default is 15 minutes, with options from 1 minute to 60, or never. Only activity inside the app counts, not system-wide idle, which is unreliable on some Linux setups and lets work in other apps keep the lock open.
- **By the computer:** when the operating system suspends or locks the screen, the app locks too (a per-account setting, on by default).

The "locked" state is held by the engine, not the page, so reloading the window doesn't undo it. To unlock, type the password again.

It is a screen lock for someone walking past. It is not a barrier against a person who can run programs as you, and the guide says so plainly.

> **Lesson.** Lock and sign-out are different tools. A lock protects the *screen* while work continues; a sign-out ends the *session*. Keep the lock state somewhere a page reload can't reset.

---

## The Locksmith (forgot my password)

**Scene.** There's no email to send a reset link to; everything is local.

The way back is a command run once from a terminal that names the account. It needs access to the computer, which is also what it would take to read the data, so it's no weaker than the login.

The account **loses its password and the secrets saved on its clusters** (SSH passwords, passphrases, API tokens), because those were guarded by that identity. Clusters, notes and settings stay. Ahmed signs in with no password and sets a new one, and a remembered sign-in is revoked at the same moment.

The clever part is what reset *doesn't* give you: it wipes the secrets instead of exposing them, so the recovery path can't be turned into a way to steal them.

> **Lesson.** A recovery path is part of the attack surface. Design it so that using it destroys the thing worth stealing.

---

## What this design does not do

Being honest is part of the design. According to the write-up:

- **Not a vault.** The keychain belongs to the computer user, so two app users sharing one computer login could, with effort, read each other's sealed secrets.
- **Some settings are shared:** panel layout, cluster order, sidebar width, notification preferences and known SSH hosts.
- **Not built yet:** a password reset without a terminal, disabling or removing an account, an admin role, online sign-in, and database-level links between tables.
- **Password hashing is tuned for a local gate**, not for resisting a leaked password database.

---

## The door that's already built: going online

The rest of the app never talks to the Clerk by name. It talks to a *role*: "someone who can create an account, sign someone in and change a password." The local Clerk, with a username and optional password, is simply the first to fill that role.

Each account also records *which* kind of Clerk vouched for it, with room for the identity that Clerk knows it by. So an online sign-in (say, through the browser with a company login) is a second Clerk filling the same role, while the screens, the Bouncer, the Cartographer, the Night Watch and the Curtain stay exactly as they are.

> **Lesson.** Depend on the role, not the implementation, and record who vouched for each identity.

---

## Recap

- Lock is not sign-out, and its state lives in the engine.
- Recovery wipes the secrets instead of exposing them.
- The honest limits are written down.
- Sign-in is a role, so a second provider can fill it later.

**Next tea talk:** [Reviewing the Design](/programming/local-app-accounts/reviewing-the-design.md), where we stop admiring it and start poking holes.