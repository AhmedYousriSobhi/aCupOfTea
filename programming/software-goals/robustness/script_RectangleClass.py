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
        