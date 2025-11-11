# Linux Admin - Under the Hood

The target of this page is to learn more deeper things that come to our minds.

## Table of Contents
- [Linux Admin - Under the Hood](#linux-admin---under-the-hood)
  - [Table of Contents](#table-of-contents)
  - [1. SCP - Why it's secured?](#1-scp---why-its-secured)
    - [How it Works Under The Hood?](#how-it-works-under-the-hood)
    - [Direction Matters](#direction-matters)
    - [Who opens the SSH Connection?](#who-opens-the-ssh-connection)
    - [What happens after SSH connects](#what-happens-after-ssh-connects)
  - [2. Directory is a Logical Container](#2-directory-is-a-logical-container)
    - [1. What the Phrase Assumes?](#1-what-the-phrase-assumes)
    - [2. What's True and what's easy to misunderstand?](#2-whats-true-and-whats-easy-to-misunderstand)
  - [3. Unix Like System ?!](#3-unix-like-system-)
    - [1. Historical Context](#1-historical-context)
    - [2. Core Traits of Unix-like Systems](#2-core-traits-of-unix-like-systems)

## 1. SCP - Why it's secured?
- The `cp` in scp comes from the Unix command cp (copy).
- But unlike cp, which copies files locally, scp allows copying across networked systems.
- The “secure” part comes from the fact that it uses SSH (Secure Shell) to handle both:
    1. **Authentication** (verifying who you are), and
    2. **Encryption** (protecting the data in transit).

So, it’s essentially: `cp + SSH = scp (a “secure” networked copy)`.

### How it Works Under The Hood?
1. **SSH As The Transport Layer**: `scp` doesn't reinvent network security; it delegates it to SSH. When you run:
    ```bash
    scp file.txt user@remote:/tmp
    ```
    1. It starts an SSH session to `remote`.
    2. SSH performs **Key exchange** (usually using RSA, ECDSA, or Ed25519) to establish a shared secret.
    3. The session is **encrypted** (commonly via AES or ChaCha20) and authenticated (via your private key or password)
    - At this point, you have got a **secure channel**; similar to what happens when you log in using `ssh`.

2. **The SCP Protocol**: Once the SSH tunnel is established, the actual file transfer happens using a **simple, custom protocol**.
    1. The **client** sends control messages like `c0644 12345 filename\n` (meaning "create a file with mode 0644 and size 12345 bytes").
    2. The **server** replies with acknowledgments (`\0` or error codes).
    3. The *file data* is streamed directly afterward, byte-for-byte.
    4. When complete, both sides send a final null byte (`\0`) to mark success.
    - So, the SSH connection acts as a secure "pipe" for these structured commands and raw bytes.

### Direction Matters
Running:
```bash
scp local.txt user@remote:/tmp/
```

Your local Machine:
1. Starts an SSH connection to `remote`.
2. On the remote system, SSH launches a command: `scp -t /tmp/`, where `-t` means "I'm the target"; expects to receive files.

Your local scp process then sends the file data to that remote process, So:
- local = sender
- Remote = receiver

Now, flipping it:
```bash
scp user@remote:/tmp/file.txt .
```
- Here, your local command wants to `fetch` a file from the remote. So the logic inverts:
1. Your local scp again open a SSH session.
2. But this time  it tells the remote host to run: `scp -f /tmp/file.txt`, where `-f` means "I'm the source"; provide files.

Now:
- Remote = Sender
- Local = Receiver

### Who opens the SSH Connection?
**YOU!!** - The machine where you run the `scp` command - always initiate the SSH connection.

Where you type:
```bash
scp local.txt user@remote:/tmp/
```
- It's said: Hey SSH, connect to `user@remote`, and once you're in, run a remote scp process for me.
- Local: starts SSH → connects to remote.
- Remote: does not initiate anything; it just receives that SSH session and executes whatever command the SSH request tells it to.

### What happens after SSH connects
Here’s the subtle part — once SSH is established, the local scp tells the remote SSH daemon to run scp in either send or receive mode depending on direction.

Let’s check both cases:

**1- Upload (local → remote)**
```bash
scp local.txt user@remote:/tmp/
```
1. Local opens SSH connection to remote.
2. Remote SSH daemon spawns scp -t /tmp/ (-t = “target mode”, i.e. receive mode).
3. Local scp sends file data to that process.

So:
- Connection initiated by: local
- Remote mode: -t (receive)
- Local mode: send

**2- Download (remote → local)**
```bash
scp user@remote:/tmp/file.txt .
```
1. Local opens SSH connection to remote (still you initiating!).
2. Remote SSH daemon spawns scp -f /tmp/file.txt (-f = “from mode”, i.e. send mode).
3. Local scp receives the file from that process.

So again:
- Connection initiated by: local
- Remote mode: -f (send)
- Local mode: receive

## 2. Directory is a Logical Container
What a catch phrase! It was from Chapter-3 in HPC book.

### 1. What the Phrase Assumes?
1. A directory isn't physical entity; it does not "contain" files on disk the way a folder contains papers.
2. It's logical, meaning it's a data structure that organize references -- essentially, **metadata** pointing to where files are actually stored.
3. It's independent of the physical layout on storage device. The same directory structure could map to files distributed across many disks or nodes (as in Lustre, BeeGFS, or GPFS).

### 2. What's True and what's easy to misunderstand?
The definition is accurate in that directories hold references to file inodes (or equivalent structures), not the file data itself. But it’s incomplete if we take “logical” too loosely:
- Directories are implemented physically on disk — usually as tables or trees of entries mapping filenames to inode numbers.
- So they’re not purely abstract; they’re a logical abstraction backed by a physical data structure.

You could reframe it as:
```
A directory is a logical mapping from human-readable names to file metadata (inodes), physically implemented through data structures managed by the filesystem’s metadata service.
```

## 3. Unix Like System ?!
A Unix-like system refers to any os that behaves similarly to the original UNIX, follows its design philosophy, and often implements its standards, but isn't necessarily derived directly from the original UNIX source code.

### 1. Historical Context
- UNIX was developed in the late 1960s at Bell Labs by Ken Thompson, Dennis Ritchie, and others.
- Over time, UNIX became both a technical model (its architecture, tools, and philosophy) and a cultural model (its simplicity, modularity, and text-based approach).

> When newer systems adopted its design ideas — but not its code, they became known as “Unix-like.”

### 2. Core Traits of Unix-like Systems
They generally share these key features:
- **File system hierarchy**: Everything is a file — devices, sockets, text, all accessed through file-like interfaces.
- **Multiuser, multitasking model**: Designed from the start for multiple users and concurrent processes.
- **Command-line shell**: Interaction primarily through text commands (e.g., bash, zsh, tcsh).
- **Small, composable utilities**: Tools that “do one thing well” and can be combined via pipes (|) and redirection.
- POSIX compliance: They follow the Portable Operating System Interface standard, which defines UNIX-like APIs and behavior.

