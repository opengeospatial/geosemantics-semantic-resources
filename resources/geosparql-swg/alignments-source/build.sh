#!/bin/bash

DIRECTORY="."
PATTERN="*.ttl"

for file in "$DIRECTORY"/$PATTERN; do
  if [ -f "$file" ]; then
    echo "Processing $file"
    kurra file reformat -f nt -o $file.nt $file
  fi
done

cat alignments.txt *.nt >> ../alignments.ttl
kurra file reformat ../alignments.ttl

rm *.nt