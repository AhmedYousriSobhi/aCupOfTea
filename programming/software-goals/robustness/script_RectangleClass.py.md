# script_RectangleClass.py

<div class="code-file">

Code file from the repository  ·  [View on GitHub](https://github.com/AhmedYousriSobhi/aCupOfTea/blob/main/programming/software-goals/robustness/script_RectangleClass.py)  ·  [Raw file](https://raw.githubusercontent.com/AhmedYousriSobhi/aCupOfTea/main/programming/software-goals/robustness/script_RectangleClass.py)

</div>

```python
""""
    Define Recatangle class.

    This script is used to illustrate unit test libarary in python
"""

# Define Rectangle Class
class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def get_area(self):
        return self.width * self.height
    
    def set_width(self, width):
        self.width = width

    def set_height(self, height):
        self.height = height
```
