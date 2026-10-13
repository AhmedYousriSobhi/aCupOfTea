# Adding a page

Every page is a markdown file in a folder. One command does the setup:

```bash
python3 .docs/tools/new_page.py
```

It asks for:

1. **Title.** It becomes the page heading and the file name (`Attention in Transformers` → `attention-in-transformers.md`).
2. **Summary**, optional. One line, shown in search results and in the folder index.
3. **Folder.** The closest existing folders are suggested first. It warns you if a similar page already exists, and it never creates a folder without asking.
4. **Tags**, optional. Pick from the tag list in `.docs/metadata/taxonomy.yaml` (Tab completes). A new tag is added only if you confirm.

It then creates the page with a short outline to fill in, adds it to the folder's `README.md` index, and regenerates the site sidebar.

To skip the questions, pass the answers as options:

```bash
python3 .docs/tools/new_page.py --title "Attention in Transformers" \
  --folder fields/deep-learning/concepts --tags transformers \
  --summary "How attention lets a model weigh every token." --yes
```

Add `--dry-run` to see the result without writing anything. Only Python 3 is needed.

## Without the script

- Use a lowercase-kebab-case file name: `my-topic.md`.
- Start the page with one `# Heading`. The sidebar shows the text after the last hyphen, so `# Deep Learning - Attention` appears as **Attention**.
- Write links root-absolute: `/fields/deep-learning/concepts/basics.md`.
- Commit images next to the page instead of linking to other sites.
- Add the page to its folder's `README.md` and run `cd .docs && ./gen_sidebar.sh`.

## Sending it

Commit on a branch cut from `dev` and open a pull request into `dev`.
