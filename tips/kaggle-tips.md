# Kaggle Tips & Tricks

## Connecting Kaggle Api (Linux)
In case of downloading dataset from Kaggle into Google Colab notebook using Kaggle Api, It is required to have user credentials to be able to connect using the Api.

The following code snipet, illustrate how to do so:

```python
!mkdir -p ~/.kaggle/ && mv kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
```

Descriptions:
- mkdir: create a new directory named .kaggle (. for been hidden),
- mv: move the json (credentials) file to the .kaggle dir.
- chmod 600: sets permissions so that, (U)ser / owner can read, can write and can't execute.
