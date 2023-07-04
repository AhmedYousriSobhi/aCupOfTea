## connecting kaggle Api (Linux)
```python
!mkdir -p ~/.kaggle/ && mv kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
```

mkdir: create a new directory named .kaggle (. for been hidden)

mv: move the json (credentials) file to the .kaggle dir

chmod 600: sets permissions so that, (U)ser / owner can read, can write and can't execute