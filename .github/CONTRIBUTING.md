# Adding a page

Every page is a markdown file in a folder. One command does the setup:

```bash
python3 .docs/tools/new_page.py
```

It asks for:

1. **Title.** It becomes the page heading and the file name (`Attention in Transformers` → `attention-in-transformers.md`).
2. **Summary**, optional. One line, shown in search results and in the folder index.
3. **Folder.** The closest existing folders are suggested first. It warns you if a similar page already exists, and it never creates a folder without asking.
4. **Type**: concept (explains an idea), guide (how to do something), reference (to look up), note, problem, project or experiment. The type most pages in that folder use is suggested.
5. **Domains**, one or two subjects such as `deep-learning` or `systems-and-hpc`. They put the page in Explore by subject. The folder's usual subjects are suggested.
6. **Tags**, optional. Pick from the tag list in `.docs/metadata/taxonomy.yaml` (Tab completes). A new tag is added only if you confirm.
7. **Level**, **prerequisites** and **related pages**, optional. `beginner` makes the page show under "Beginner friendly" in Start here. Prerequisites are ids of pages to read first, which builds a learning path; related pages show as "See also" under the title. Both take page ids (Tab completes).

You don't enter a reading time: the site works it out from the text (200 words a minute, code not counted) and shows it under the title, so it stays right when the page changes.

It then creates the page with a short outline to fill in, adds it to the folder's `README.md` index (a `File | Description` table, or a list of links), and regenerates the site sidebar.

To skip the questions, pass the answers as options:

```bash
python3 .docs/tools/new_page.py --title "Attention in Transformers" \
  --folder fields/deep-learning/concepts --tags transformers \
  --summary "How attention lets a model weigh every token." --level intermediate \
  --type concept --domains deep-learning --related sequence-models --yes
```

Add `--dry-run` to see the result without writing anything. Only Python 3 is needed.

## When the page is written

```bash
python3 .docs/tools/new_page.py --check fields/deep-learning/concepts/attention-in-transformers.md
```

It shows the reading time readers will see, whether the page counts as a quick read (10 minutes or less), and what is still missing: outline notes from the template, empty sections, a summary, type, domains, tags or level, pictures described only as "image", and relative links that break on the site.

## Without the script

- Use a lowercase-kebab-case file name: `my-topic.md`.
- Start the page with one `# Heading`. The sidebar shows the text after the last hyphen, so `# Deep Learning - Attention` appears as **Attention**.
- Write links root-absolute: `/fields/deep-learning/concepts/basics.md`.
- Keep your own images in the repo: put them in an `images/` folder next to the page and link them relative to the page, `![caption](images/my-topic-01.png)`. Root-absolute paths do not work for images on the site. Pictures that belong to someone else stay links to their source.
- Add the page to its folder's `README.md` and run `cd .docs && ./gen_sidebar.sh`.

## Sending it

Commit on a branch cut from `dev` and open a pull request into `dev`.

By contributing, you agree that your writing is licensed under [CC BY 4.0](../LICENSE) and your code under the [MIT License](../LICENSE-CODE), as described in the README.
