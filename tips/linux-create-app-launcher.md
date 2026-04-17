# Tip: Linux Create App Launcher

# Table of Content
- [Tip: Linux Create App Launcher](#tip-linux-create-app-launcher)
- [Table of Content](#table-of-content)
- [Steps to Create App Launcher](#steps-to-create-app-launcher)
- [Reference](#reference)

# Steps to Create App Launcher
1. Use Gedit to create an app launcher for Iris.
    ```bash
    sudo gedit /usr/share/applications/iris.desktop
    ```

2. Add the following lines in this file.
    ```bash
    [Desktop Entry]
    Name=Iris
    Comment=Eye Protection Software
    Exec=/opt/iris/Iris.sh
    Type=Application
    Terminal=false
    Icon=/opt/iris/iris.png
    NoDisplay=false
    ```
3. Save and close this file. Then Download the Iris logo file.
    ```bash
    wget -O iris.png https://iristech.co/wp-content/themes/iris/img/Logo.png
    ```
4. Move it to /opt/iris/ directory.
    ```bash
    sudo mv iris.png /opt/iris/
    ```

# Reference
- This tutorial was taken from the instructions to setup [Iris eye care app](https://www.linuxbabe.com/desktop-linux/protect-your-eyes-from-computer-screen-with-iris) on Linux system