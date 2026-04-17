#!/bin/bash

# Configuration - Output stays in the current directory (.docs/)
OUTPUT="_sidebar.md"

# Updated Exclusions: now ignoring .docs and .github
EXCLUDE_DIRS="\.git|\.github|node_modules|\.docs|docs" 
EXCLUDE_FILES="_sidebar.md|_navbar.md|index.html"

# Initialize the sidebar file with the Home link
echo "* [Home](README.md)" > $OUTPUT

generate_sidebar() {
    local dir=$1
    local indent=$2

    # List items from the target directory, excluding hidden files
    find "$dir" -maxdepth 1 -not -path '*/.*' | sort | while read -r path; do
        
        # Skip the directory itself
        if [ "$path" == "$dir" ]; then continue; fi
        
        local base=$(basename "$path")
        
        # Check against exclusions
        if [[ "$base" =~ $EXCLUDE_DIRS || "$base" =~ $EXCLUDE_FILES ]]; then continue; fi

        if [ -d "$path" ]; then
            # Directory: Clean filename for the bold label
            local folder_name=$(echo "$base" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')
            echo "${indent}* **$folder_name**" >> $OUTPUT
            
            # Recurse
            generate_sidebar "$path" "  $indent"
        elif [[ "$base" == *.md ]]; then
            
            # Skip only the root README.md (which is ../README.md from here)
            if [[ "$path" == "../README.md" ]]; then continue; fi

            # File: Try to extract the first # Header
            local header=$(grep -m 1 "^# " "$path" | sed 's/^# //')
            
            # Fallback to cleaned filename
            if [ -z "$header" ]; then
                header=$(echo "${base%.md}" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')
            fi

            # --- CRITICAL MODIFICATION ---
            # Remove the "../" prefix so the link is correct for index.html in root
            local clean_link="${path#../}"
            echo "${indent}* [$header]($clean_link)" >> $OUTPUT
        fi
    done
}

# Start recursion from the parent directory
generate_sidebar ".." ""

echo "Sidebar updated inside .docs/ using paths relative to root."