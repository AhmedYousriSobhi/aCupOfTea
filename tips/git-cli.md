# Git Command Line Interface (CLI)

In the context of Git, "gh" refers to the GitHub CLI tool, which is a command-line interface for interacting with GitHub repositories. It provides a convenient way to manage GitHub-specific features, such as issues, pull requests, and releases, directly from your terminal. The GitHub CLI is available for macOS, Windows, and Linux, and it can be installed using a package manager or by downloading the binary from the GitHub CLI website.

## CLI Benefits
Here are some of the benefits of using the GitHub CLI:
|Benefit|Details|
|-|-|
|Efficiency| It allows you to perform GitHub tasks without having to switch between the terminal and a web browser.
|Automation| You can use scripts to automate repetitive tasks, such as creating issues or updating pull requests.
|Customization| You can create custom aliases and extensions to personalize your GitHub CLI experience.

## HTTP vs CLI Cloning
Normal HTTP cloning and gh clone are both methods for cloning a Git repository, but there are some key differences between the two.

Normal HTTP cloning involves downloading the contents of the repository directly from the Git server using the HTTP protocol. This method is simple to use, but it can be slow and unreliable, especially for large repositories.

gh clone is a command provided by the GitHub CLI tool that uses GitHub-specific APIs to clone repositories. This method is more efficient and reliable than normal HTTP cloning, and it also supports additional features, such as cloning private repositories and using SSH authentication.

Here is a table summarizing the key differences between normal HTTP cloning and gh clone:
|Feature|	Normal HTTP cloning|	gh clone|
|-|-|-|
Protocol|	HTTP|	GitHub-specific APIs|
Speed|	Slow|	Efficient|
Reliability|	Unreliable|	Reliable|
Supported features|	Cloning public repositories|	Cloning public and private repositories, using SSH authentication

In general, it is recommended to use gh clone for cloning Git repositories whenever possible. It is a more efficient, reliable, and feature-rich method than normal HTTP cloning.

## Usage Examples
Here are some examples of how to use the GitHub CLI:
|Action|Command|
|-|-|
|Create an issue| gh issue create "Describe the issue here"
|List open pull requests| gh pr list
|Create a new release| gh release create "Version 1.0.0" -t "v1.0.0"

Here is an example of how to clone a repository using gh clone:
Bash
```
gh clone https://github.com/google/bard
```

This will clone the google/bard repository to the current directory. If you want to clone the repository to a different directory, you can specify the directory name as an argument to the gh clone command. For example, the following command will clone the google/bard repository to the directory named bard:
Bash
```
gh clone https://github.com/google/bard bard
```

## How to Use?
Here are the general steps on how to use the GitHub CLI:

1. Install the GitHub CLI:

    -  For macOS, download the binary from the GitHub CLI website or use Homebrew to install it.
    -  For Windows, download the installer from the GitHub CLI website or use Chocolatey to install it.
    -  For Linux, use your distribution's package manager to install the GitHub CLI package.

2. Authenticate with GitHub:
    - Open a terminal window and run the command gh auth login.
    - Follow the on-screen instructions to sign in to your GitHub account.
    - GitHub CLI will store your credentials securely.

3. Use GitHub CLI commands:
    - There are many different GitHub CLI commands available for managing issues, pull requests, repositories, and other GitHub features.
    - You can find a list of all available commands by running the command gh help.
    - For help with a specific command, run the command gh help <command>.

4. Customize your GitHub CLI experience:
    - You can create custom aliases for frequently used commands.
    - You can install extensions to add additional features to GitHub CLI.
    - You can configure GitHub CLI settings to personalize your experience.

Here are some examples of how to use GitHub CLI commands:
- Create an issue: gh issue create "Describe the issue here"
- List open pull requests: gh pr list
- Create a new release: gh release create "Version 1.0.0" -t "v1.0.0"
- Clone a repository: gh clone https://github.com/google/bard

For more information on the GitHub CLI, please refer to the official documentation: https://github.com/cli/cli

## Steps

1. In case of any unwanted SSH Key file, Start by removing them:
    - Open a terminal window and navigate to the directory where your SSH key files are stored.
    - Locate the id_rsa and id_rsa.pub files.
    - Delete both files using the rm command.
    - For example, to delete the id_rsa and id_rsa.pub files, you would run the following commands:
```
rm ~/.ssh/id_rsa
rm ~/.ssh/id_rsa.pub
```
2. Remove the SSH key from your GitHub account:
    - Go to your GitHub account settings.
    - Click on the "SSH and GPG keys" tab.
    - Find the SSH key that you want to remove and click on the "Delete key" button.

3. Re-generate the SSH key:
    - Open a terminal window and run the following command:
```
ssh-keygen
```

- When prompted, enter a filename for the key pair.
- Then, enter a passphrase for the key. This is optional, but it is recommended for security reasons.
- Your SSH key pair will be generated.
- The public key will be saved to a file called id_rsa.pub, and the private key will be saved to a file called id_rsa.

4. Add the public key to your GitHub account:
    - Copy the contents of the id_rsa.pub file to your clipboard.
    - Go to your GitHub account settings.
    - Click on the "SSH and GPG keys" tab.
    - Click on the "New SSH key" button.
    - Paste the contents of your clipboard into the "Key" field.
    - Give your key a title, such as "My new SSH key for GitHub".
    - Click on the "Add SSH key" button.

5. Re-configure GitHub CLI to use SSH:
    - Open a terminal window and run the following command:

```
git config --global core.sshCommand "ssh -o IdentityFile=$HOME/.ssh/yousri_per"
```
- This will configure GitHub CLI to use the id_rsa key for SSH authentication.

6. Retry the gh command:
    - Once you have completed these steps, you should be able to retry the gh command without any errors.

This process will ensure that you start with a fresh set of SSH keys and that your GitHub account is properly configured to use them.
