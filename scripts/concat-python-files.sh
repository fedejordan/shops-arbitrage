#!/bin/bash

output="all_python_backend_code.txt"
echo "" > "$output"

# Concatenar archivos .java
find . -name "*.py" | while read file; do
    echo "Agregando archivo: $file"
    echo "// --- FILE: $file ---" >> "$output"
    cat "$file" >> "$output"
    echo -e "\n" >> "$output"
done

# Concatenar archivos .xml
find . -name "*.xml" | while read file; do
    echo "Agregando archivo: $file"
    echo "<!--- FILE: $file --->" >> "$output"
    cat "$file" >> "$output"
    echo -e "\n" >> "$output"
done
