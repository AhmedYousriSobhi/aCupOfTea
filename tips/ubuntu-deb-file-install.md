<!-- related-block -->
<nav class="crumbs" aria-label="Breadcrumb"><a href="#/tips/">Tips</a></nav>

# Tips - Ubuntu Debian File Installation

<!-- related-block -->
<div class="reading-time">1 min read · Updated 8 Nov 2026</div>


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
