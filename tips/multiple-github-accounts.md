# for windows you need to have OpenSSH
# this method uses config file

1. from the root directory go to .ssh 
```bash
cd ~/.ssh
```

2. for account 1 generate the ssh with 
```bash
ssh-keygen
```
you can set the passphrase if you want, here using the default 
you should get id_rsa and id_rsa.pub

3. copy the public key "id_rsa.pub" and set it to the corresponding github account in settings > SSH and GPG keys
```bash
cat id_rsa.pub
```

4. for account 2 you need to define a name when creating the key so it won't overwrite it
```bash
ssh-keygen -f work_id_rsa
```
same if you want to set passphrase you can do it, but using default here.

5. now if you "ls" or "dir" you should see:
```bash
id_rsa  id_rsa.pub  work_id_rsa  work_id_rsa.pub
```

6. same copy the work_id_rsa.pub to your second github

7. now we need a config file in order for git to distinguish between accounts
```bash
vi config
```

for windows
```bash
notepad config
mv config.txt config
```
the renaming of config is due to notepad saving the file as .txt

8. inside the file:
```bash
# my personal account
Host github.com
    HostName github.com
    IdentityFile ~/.ssh/id_rsa

# my work account
Host github.com-work
    HostName github.com
    IdentityFile ~/.ssh/work_id_rsa
```
a side node this can work with gitlab, you need to change github to gitlab, can work with both at the same time too.

9. if you want to clone from personal you use default ssh you copy from github
```bash
git clone git@github.com:AhmedYousriSobhi/aCupOfTea.git
```

if you want to use your work then:
```bash
git clone git@github.com-work:AhmedYousriSobhi/aCupOfTea.git
```

10. when you clone a repo for the first time using this method you need to set the name and email so it won't use the default name and email which here is personal
```bash
git config user.name "github account name"
git config user.email "github email"
```
