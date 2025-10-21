# Tips: Markdown
# Table of Content
- [Tips: Markdown](#tips-markdown)
- [Table of Content](#table-of-content)
- [Add "Open in Colab" Button](#add-open-in-colab-button)
- [Add General Button](#add-general-button)
- [Convert Markdown to .rst format](#convert-markdown-to-rst-format)
- [Resources](#resources)

# Add "Open in Colab" Button
Here is a markdown syntax to create a "Open in Colab" button
```md
<a href="NOTEBOOK_URL" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>
```

Here is an example for Notebook-04 in [Pytorch DeepLearning course](https://github.com/mrdbourke/pytorch-deep-learning):

<a href="https://colab.research.google.com/github/mrdbourke/pytorch-deep-learning/blob/main/04_pytorch_custom_datasets.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# Add General Button
Here is the markdown syntax to create a "General Button"
```md
<a href="https://nbviewer.org/github/user/repo/blob/main/notebook.ipynb" target="_blank" 
   style="background-color:#f5f5f5;border-radius:6px;padding:6px 12px;text-decoration:none;
          color:#333;border:1px solid #ccc;">
   View on nbviewer
</a>
```

<a href="https://nbviewer.org/github/user/repo/blob/main/notebook.ipynb" target="_blank" 
   style="background-color:#f5f5f5;border-radius:6px;padding:6px 12px;text-decoration:none;
          color:#333;border:1px solid #ccc;">
   View on nbviewer
</a>

# Convert Markdown to .rst format
- To convert .md file format to .rst file, this could be done with:
   ```bash
   pandoc input.md -f markdown -t rst -o output.rst
   ```
   - Make sure to install the [*pandoc* packages](https://pandoc.org/installing.html) on the system: *sudo apt ./pandoc-<version>-amd64.deb*  
- To convert .rst file into html file to review, use *rst2html* command:
   ```bash
   rst2html input.rst output.html
   ```

# Resources
- In [markdownguide](https://www.markdownguide.org/basic-syntax/#overview), illustrate the basic syntax in markdown design, including all tips to do and not to do.
