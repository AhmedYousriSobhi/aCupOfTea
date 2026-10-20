
# Sign-In Hygiene: How the Clerk Says "No" Without Giving Anything Away

<!-- related-block -->
<div class="reading-time">5 min read</div>
<!-- related-block -->
<div class="related-strip">

**Read first:** [Two People, One Laptop: What Accounts Should (and Shouldn't) Promise](/programming/local-app-accounts/threat-model-and-first-launch.md)  ·  **Read next:** [Who's Home, and What May They Touch? Sessions and Two Walls](/programming/local-app-accounts/sessions-and-two-walls.md)

</div>


*Local App Accounts, tea talk 2 of 6. Previous: [Threat Model and First Launch](/programming/local-app-accounts/threat-model-and-first-launch.md). Next: [Sessions and Two Walls](/programming/local-app-accounts/sessions-and-two-walls.md).*

Ahmed comes back the next morning, types his password and presses Enter. In the fraction of a second that follows, the Clerk does four things he never notices, and each one closes a small leak. This talk is about those four things.

---

## The one-sentence version

**Most of sign-in hygiene is making different failures look identical: in text, in timing and in counting.**

---

## Words you'll meet

| Term | Plain meaning |
| --- | --- |
| **Hash** | A one-way scramble of a password. You can check a guess against it, but you can't run it backwards |
| **Salt** | Random extra data mixed into each hash, so two identical passwords don't produce identical hashes |
| **Memory-hard hash** | A hash (scrypt, Argon2id) that is deliberately slow and RAM-hungry, so guessing millions of passwords gets expensive |
| **Timing attack** | Learning a secret from *how long* something takes, not from what it says |
| **User enumeration** | Using differences in errors or timing to learn which usernames exist |
| **Throttling vs lockout** | Throttling only slows repeated attempts; lockout blocks the account after N failures |

---

## Detail 1: slow, self-describing hashes

Passwords are scrambled with **scrypt**, taking about a tenth of a second per check. The stored result records its *own* settings, so the app can raise the cost later and quietly upgrade an entry the next time its owner signs in.

```js
// stored as: scrypt$<N>$<r>$<p>$<salt>$<hash>
// On sign-in:
//   1. read N, r, p and salt out of the record
//   2. hash the attempt with those same settings
//   3. compare in constant time
//   4. if the stored settings are weaker than today's policy, rehash and save
```

*(A sketch of the idea, not production code.)*

Why slow? A normal hash is fast, which is exactly what a password cracker wants. scrypt and Argon2id are built to be slow *and* to need a lot of RAM per guess, so an attacker can't simply buy more cheap chips.

**How slow is slow enough?** OWASP's Password Storage Cheat Sheet recommends **Argon2id** first. If it isn't available, it says to use scrypt with a cost of at least 2^17, a block size of 8 and parallelism of 1. A tenth of a second usually means defaults well below that. The original design says it tuned for comfort, because the login protects a door that encrypts nothing. That is defensible, and because each record stores its own settings, raising them later costs one line of code. (Your runtime's default memory ceiling may need raising to use the larger setting, so check its docs.)

---

## Detail 2: unknown usernames cost the same

Type a name that doesn't exist and the Clerk *still* checks your password, against a decoy. Otherwise a faster "no" would reveal which accounts exist.

If "no such user" returns in 1 ms and "wrong password" takes 100 ms, an attacker can stopwatch their way to a list of valid usernames. Doing the same work either way closes that leak. OWASP's Authentication Cheat Sheet describes the same defence: the code should go through the same process whatever the user or password is.

---

## Detail 3: one message for every failure

Wrong password or no such user, the answer is identical: *"Wrong username or password."* The red ring and the little shake on the password field are the same too. For screen reader users, the sentence is announced from a visually hidden alert, so nobody is left in silence.

OWASP's guidance is the same: respond with a generic message whether or not the account exists, for login, password reset and recovery alike.

---

## Detail 4: the Slow Clerk

After four wrong passwords you start waiting: one second, then two, four, eight, doubling up to a cap of fifteen minutes. Two clever choices make this interesting:

- It counts per username **whether or not the account exists**, so the waiting message can't be used to discover accounts either.
- It lives **in memory on purpose**. Restart the app and it's a fresh start. The honest trade-off: someone at the keyboard could keep a username waiting for fifteen minutes, but nobody can lock Ahmed out *forever*.

Why not a hard lockout? OWASP lists the lockout threshold, the observation window and the duration as the parameters to weigh. A fixed, long lockout is easy to abuse against a victim. A capped, doubling delay is a common compromise: it slows guessing without giving an attacker a way to lock someone out for good. (That last comparison is design reasoning, not an OWASP quote.)

---

## Recap

| Leak | Plug |
| --- | --- |
| Fast hashes are cheap to guess | Slow, memory-hard hash with self-describing settings |
| Timing reveals which usernames exist | Decoy check for unknown users |
| Error text reveals which usernames exist | One identical message |
| Waiting message reveals which usernames exist | Throttle counted per username, existing or not |

**Next tea talk:** [Sessions and Two Walls](/programming/local-app-accounts/sessions-and-two-walls.md), where the password is right and the real separation begins.

---

## References

- OWASP Cheat Sheet Series, [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): Argon2id first, then scrypt at N of at least 2^17, r of 8 and p of 1
- OWASP Cheat Sheet Series, [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html): generic error messages, equal processing for known and unknown accounts, lockout parameters