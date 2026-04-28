#!/bin/bash

# Configuration - Output stays in the current directory (.docs/)
OUTPUT="_sidebar.md"

# Updated Exclusions
EXCLUDE_DIRS="\.git|\.github|node_modules|\.docs|docs" 
EXCLUDE_FILES="_sidebar.md|_navbar.md|index.html"

# Initialize the sidebar file with the Home link
echo "* [Home](README.md)" > $OUTPUT

generate_sidebar() {
    local dir=$1
    local indent=$2

    # Temporary arrays to manage ordering
    local folders=()
    local files=()
    local overview_item=""

    # 1. Collect and categorize items in the current directory
    # Use while loop to fill arrays, handling spaces in filenames safely
    while IFS= read -r path; do
        if [ "$path" == "$dir" ]; then continue; fi
        
        local base=$(basename "$path")
        if [[ "$base" =~ $EXCLUDE_DIRS || "$base" =~ $EXCLUDE_FILES ]]; then continue; fi

        if [ -d "$path" ]; then
            folders+=("$path")
        elif [[ "$base" == *.md ]]; then
            # --- MODIFICATION 1: Extraction Logic ---
            local header=$(grep -m 1 "^# " "$path" | sed 's/^# //')
            
            # If dash exists, take everything after the LAST dash
            if [[ "$header" == *"-"* ]]; then
                header="${header##*-}"
            fi
            
            # Trim leading/trailing whitespace
            header=$(echo "$header" | xargs)

            # Fallback to cleaned filename if header is empty
            if [ -z "$header" ]; then
                header=$(echo "${base%.md}" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')
            fi

            local final_link="${path#../}"
            local entry="${indent}* [$header]($final_link)"

            # --- MODIFICATION 2: Order "Overview" to top ---
            # Check if title is "Overview" (case-insensitive)
            if [[ "${header,,}" == "overview" ]]; then
                overview_item="$entry"
            else
                files+=("$entry")
            fi
        fi
    done < <(find "$dir" -maxdepth 1 -not -path '*/.*' | sort)

    # 2. Output to _sidebar.md in specific order
    
    # First: The Overview file for this directory
    if [ -n "$overview_item" ]; then
        echo "$overview_item" >> $OUTPUT
    fi

    # Second: All other Markdown files
    for f in "${files[@]}"; do
        echo "$f" >> $OUTPUT
    done

    # Third: Directories (and recurse)
    for d in "${folders[@]}"; do
        local base=$(basename "$d")
        local folder_name=$(echo "$base" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')
        echo "${indent}* **$folder_name**" >> $OUTPUT
        generate_sidebar "$d" "  $indent"
    done
}

# Start recursion from the parent directory
generate_sidebar ".." ""

echo "Sidebar updated: Titles parsed after last dash and 'Overview' prioritized."