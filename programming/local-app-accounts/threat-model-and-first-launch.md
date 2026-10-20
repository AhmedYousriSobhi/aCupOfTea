
# Two People, One Laptop: What Accounts Should (and Shouldn't) Promise

<!-- related-block -->
<div class="reading-time">4 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read next:** [Sign-In Hygiene: How the Clerk Says "No" Without Giving Anything Away](/programming/local-app-accounts/sign-in-hygiene.md)

</div>


*Local App Accounts, tea talk 1 of 6. Next: [Sign-In Hygiene](/programming/local-app-accounts/sign-in-hygiene.md).*

Picture a shared workstation in a lab. **Ahmed** runs training jobs. **Abdelrahman** babysits the storage. Both use the same desktop app, and before accounts existed they opened the same window and saw the same clusters, the same notes and the same saved passwords. Comfortable, right up to the moment Abdelrahman's reminder to *"delete the scratch data"* pops up on Ahmed's screen while he is sharing it in a meeting.

This series follows what happens when that app learns to tell the two of them apart. This first talk is about the part that comes *before* any code: deciding what the feature is for.

---

## The one-sentence version

**Accounts in a local app are a gate and a separator, not a vault: they keep each person's workspace out of the other person's view, and give you a lock for when you step away.**

---

## Words you'll meet

| Term | Plain meaning |
| --- | --- |
| **Threat model** | A short answer to "who am I defending against, and who am I not?" |
| **Authentication** | Proving who you are ("it's really Ahmed") |
| **Authorization** | Deciding what that person may do ("Ahmed may edit *his* clusters") |

---

## The honest disclaimer

The most useful sentence in the whole design is a *negative* one. Accounts here:

- **Do** keep Ahmed's workspace out of Abdelrahman's view and out of his way.
- **Do not** stop anyone who can read your files *as you* on the operating system. Saved secrets are sealed by the computer's keychain, and the keychain belongs to the computer user, not the app user.

So the app protects **who sees what inside the app**, plus **a lock for the moment you step away**. That is the whole contract. The threat model is "the other person using this app", not "an attacker with full control of the computer."

> **Lesson.** Write the threat model before the feature. A modest, honest promise is much easier to keep than an ambitious, vague one, and every later decision gets judged against it.

---

## The cast

Every responsibility gets a character, which makes the design easy to hold in your head. They'll keep turning up in the next five talks:

| Character | Their job | Appears in |
| --- | --- | --- |
| The Doorman | Decides which screen you get: sign-up, sign-in, claim, or the app | This talk |
| The Clerk | Checks who you say you are | Talk 2 |
| The Slow Clerk | Makes password guessing expensive | Talk 2 |
| The Memory | Knows who's signed in, in memory only | Talk 3 |
| The Bouncer | Inspects every request and asks "is that yours?" | Talk 3 |
| The Cartographer | Draws the map of what you may see, down in the database | Talk 3 |
| The Night Watch | Runs background monitors, but only while somebody is home | Talk 4 |
| The Curtain | The lock screen | Talk 5 |
| The Locksmith | Gets you back in when you forget your password | Talk 5 |

---

## The very first launch

**Scene.** Fresh install, no accounts. The Doorman sees an empty list of people, so the first thing you get is **Create your account**.

Two small decisions are worth a second look.

**The password is optional.** Plenty of single-user laptops don't want one. An account without a password simply opens with an empty one. The login is a gate for people who *chose* to have one, not a requirement the app imposes on everyone.

**The first account adopts the empty profile.** A fresh install already has one empty profile the app made for itself. Asking a brand-new user to "claim" an empty profile would be silly, so the first account just takes it.

The rules stay tiny: a username is 3 to 32 characters (letters, digits, dot, underscore, dash, starting and ending with a letter or digit), and a password, if you set one, is 8 to 256 characters. The rules live behind an info icon so the form stays calm.

> **Lesson.** Don't make the common case (one person, one laptop) pay for a feature built for the uncommon one.

---

## Recap

- State the threat model first, including what you are *not* protecting.
- Keep the first-run path frictionless: optional password, and the first account adopts the empty profile.

**Next tea talk:** [Sign-In Hygiene](/programming/local-app-accounts/sign-in-hygiene.md), where the Clerk learns to say "no" without giving anything away.