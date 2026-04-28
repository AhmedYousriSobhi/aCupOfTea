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
    while IFS= read -r path; do
        if [ "$path" == "$dir" ]; then continue; fi
        
        local base=$(basename "$path")
        if [[ "$base" =~ $EXCLUDE_DIRS || "$base" =~ $EXCLUDE_FILES ]]; then continue; fi

        if [ -d "$path" ]; then
            folders+=("$path")
        elif [[ "$base" == *.md ]]; then
            # --- FILE HEADER EXTRACTION ---
            local header=$(grep -m 1 "^# " "$path" | sed 's/^# //')
            
            local file_title="$header"
            # If dash exists, take the part AFTER the last dash
            if [[ "$header" == *"-"* ]]; then
                file_title="${header##*-}"
            fi
            file_title=$(echo "$file_title" | xargs) # Trim whitespace

            # Fallback for file title if header is missing
            if [ -z "$file_title" ]; then
                file_title=$(echo "${base%.md}" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')
            fi

            local final_link="${path#../}"
            local entry="${indent}* [$file_title]($final_link)"

            # --- ORDERING: Force "Overview" to top ---
            if [[ "${file_title,,}" == "overview" ]]; then
                overview_item="$entry"
            else
                files+=("$entry")
            fi
        fi
    done < <(find "$dir" -maxdepth 1 -not -path '*/.*' | sort)

    # 2. Output files (Overview always first)
    if [ -n "$overview_item" ]; then
        echo "$overview_item" >> $OUTPUT
    fi
    for f in "${files[@]}"; do
        echo "$f" >> $OUTPUT
    done

    # 3. Process Directories
    for d in "${folders[@]}"; do
        local base=$(basename "$d")
        local folder_display_name=""

        # --- FOLDER NAMING LOGIC ---
        local readme_file="$d/README.md"
        if [ -f "$readme_file" ]; then
            local readme_header=$(grep -m 1 "^# " "$readme_file" | sed 's/^# //')
            
            if [ -n "$readme_header" ]; then
                if [[ "$readme_header" == *"-"* ]]; then
                    # If dash exists, take everything BEFORE the last dash
                    folder_display_name="${readme_header%-*}"
                else
                    # If no dash exists (e.g., just "# Business"), take the whole header
                    folder_display_name="$readme_header"
                fi
                folder_display_name=$(echo "$folder_display_name" | xargs)
            fi
        fi

        # Final Fallback to folder name from filesystem
        if [ -z "$folder_display_name" ]; then
            folder_display_name=$(echo "$base" | sed 's/[-_]/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)} 1')
        fi

        echo "${indent}* **$folder_display_name**" >> $OUTPUT
        
        # Recurse
        generate_sidebar "$d" "  $indent"
    done
}

# Start recursion
generate_sidebar ".." ""

echo "Sidebar updated: Logic applied for single-word headers and dash-separated titles."