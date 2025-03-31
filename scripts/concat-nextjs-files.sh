#!/bin/bash

output="all_nextjs_frontend_code.txt"
echo "" > "$output"

# Concatenar archivos .tsx
find . -path "./node_modules" -prune -o -name "*.tsx" -print | while read file; do
    echo "Agregando archivo: $file"
    echo "// --- FILE: $file ---" >> "$output"
    cat "$file" >> "$output"
    echo -e "\n" >> "$output"
done

# Concatenar archivos .ts
find . -path "./node_modules" -prune -o -name "*.ts" -print | while read file; do
    echo "Agregando archivo: $file"
    echo "<!--- FILE: $file --->" >> "$output"
    cat "$file" >> "$output"
    echo -e "\n" >> "$output"
done

# Concatenar archivos .json
find . -path "./node_modules" -prune -o -name "*.json" -print | while read file; do
    echo "Agregando archivo: $file"
    echo "<!--- FILE: $file --->" >> "$output"
    cat "$file" >> "$output"
    echo -e "\n" >> "$output"
done