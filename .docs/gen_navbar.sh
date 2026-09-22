#!/bin/bash

OUTPUT="_navbar.md"
GITHUB_REPO="AhmedYousriSobhi/aCupOfTea"
GITHUB_PROFILE="https://github.com/AhmedYousriSobhi"
LinkedIn_PROFILE="https://www.linkedin.com/in/ahmedyousrisobhi/"

# 1. Start with the Home link
echo "* [🏠 Home](README.md)" > $OUTPUT
echo "" >> $OUTPUT

# 2. Categorize Top-Level Folders
echo "* 📂 Categories" >> $OUTPUT

# Find top-level directories (depth 1) and create dropdown links
# We exclude hidden folders and common config folders
find .. -maxdepth 1 -type d -not -path '*/.*' -not -path '..' | sort | while read -r dir; do
    name=$(basename "$dir")
    
    # Clean the name (e.g., "hpc_storage" -> "Hpc Storage")
    clean_name=$(echo "$name" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')
    
    # Add as a sub-item under Categories (Docsify creates a dropdown)
    # We link to the folder's README if it exists, otherwise just the folder
    if [ -f "$dir/README.md" ]; then
        echo "  * [$clean_name]($name/README.md)" >> $OUTPUT
    else
        echo "  * [$clean_name]($name/)" >> $OUTPUT
    fi
done

echo "" >> $OUTPUT

# 3. Add External/Social Links
echo "* 🔗 External" >> $OUTPUT
echo "  * [GitHub](https://github.com/$GITHUB_REPO)" >> $OUTPUT
echo "  * [Profile]($GITHUB_PROFILE)" >> $OUTPUT
echo "  * [LinkedIn]($LinkedIn_PROFILE)" >> $OUTPUT

echo "Done! _navbar.md generated."