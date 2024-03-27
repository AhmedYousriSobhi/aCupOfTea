# Ubuntu Debian File Installation

## Table of Content
- [Ubuntu Debian File Installation](#ubuntu-debian-file-installation)
  - [Table of Content](#table-of-content)
  - [Install deb file from Command Line](#install-deb-file-from-command-line)
  - [Steps to Fix Dependencies Error](#steps-to-fix-dependencies-error)

## Install deb file from Command Line
To install deb package from CL, simply run:
```
sudp dpkg -i <package.deb>
```

## Steps to Fix Dependencies Error
1. Instruct dpkg to "fix" itself.
    ```
    sudo dpkg --configure -a
    ```

2. This will instruct apt-get to correct dependencies and continue to configure your packages
    ```
    sudo apt-get -f install
    ```

3. Reinstall the package
    ```
    sudo dpkg -i <package.deb>
    ```

Note:
- In case of using apt install:
  ```
    sudo apt install <package> --reinstall
  ```
