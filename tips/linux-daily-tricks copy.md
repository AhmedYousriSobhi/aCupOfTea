# Tips - Linux daily Tricks

These are some tips and tricks I usually need in my daily work, so I tried to document them here.

# Table of Tricks
- [Tips - Linux daily Tricks](#tips---linux-daily-tricks)
- [Table of Tricks](#table-of-tricks)
  - [To delete file content in ***vi***](#to-delete-file-content-in-vi)
  - [To search for Something](#to-search-for-something)
  - [To get OS info you are using:](#to-get-os-info-you-are-using)
  - [To know Which Shell you Use](#to-know-which-shell-you-use)
  - [To get OS version](#to-get-os-version)
  - [To identify root dir](#to-identify-root-dir)
  - [tmux Use mouse to scroll](#tmux-use-mouse-to-scroll)
  - [To Update Nvidia Driver](#to-update-nvidia-driver)
  - [Packages Management Related](#packages-management-related)

## To delete file content in ***vi***
```bash
# Enter the script
vi <script-name>

# to get to the first line in the file.
gg 

# to enter visualize mode.
v 

# to select all.
G 

# delete.
dd 
```

## To search for Something
```bash
find / -name <target-dir-to-find> 2>/dev/null
```

## To get OS info you are using:
```bash
uname -a
```

## To know Which Shell you Use
```bash
echo $0
```

## To get OS version
```bash
cat /etc/os-release
```

## To identify root dir
```bash
findmnt / -o source -n
```

## tmux Use mouse to scroll
```bash
# To use your mouse in this mode (called copy mode) press ^b + : and enter following:

setw -g mouse on
```

Reference: Scroll shell output with mouse in tmux. [https://superuser.com/a/217269](https://superuser.com/a/217269)

## To Update Nvidia Driver
```bash
dpkg -l | grep nvidia

sudo apt-get --purge remove nvidia*

sudo apt-get --purge remove "*nvidia*"

sudo apt autoremove

sudo apt autoclean

sudo reboot
```
- Then use the default linux nvidia driver supported.

## Packages Management Related
- Search for package dependencies
  ```bash
  dnf repoquery --requires <packag-ename>
  ```
- Search for specific package source
  ```bash
  yum provides <package>
  # e.g
  yum provides ld-linux.so.2
  ```
- Search for packages that requires certain <packages>
  ```bash
  # For Red Hat/Fedora
  dnf repoquery --whatrequires gcc
  # or
  yum deplist gcc | grep dependent

  # For Debian/Ubuntu based systems
  sudo apt-get install apt-rdepends
  dnf repoquery --whatrequires gcc
  ```