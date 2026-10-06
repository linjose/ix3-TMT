#!/bin/bash

# Usage: ./convert.sh <path-to-file>

set -euo pipefail

path="$1"
filename="$(basename "$path")"
ext="${filename##*.}"
outdir="converted_jpg"
mkdir -p "$outdir"

echo "Input file: $path"
echo "Extension: $ext"

to_pdf_and_convert() {
  soffice --headless --convert-to pdf "$path" --outdir "$outdir"
  pdf_file="$outdir/${filename%.*}.pdf"
  convert -verbose -density 150 "$pdf_file" -quality 100 "$outdir/${filename%.*}.jpg"
  rm -f "$pdf_file"
}

case "$ext" in
  ppt|pptx)
    to_pdf_and_convert
    ;;
  key)
    echo "Keynote format detected. Please convert .key to .pdf manually (Keynote export)."
    ;;
  *)
    echo "Unsupported file type: $ext"
    ;;
esac

echo "Done. Please check folder $outdir"
