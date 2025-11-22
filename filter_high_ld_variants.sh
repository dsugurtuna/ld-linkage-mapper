#!/bin/bash
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# Script: filter_high_ld_variants.sh
# Description: Parses the raw output from LDProxy and filters for variants
#              that are perfect proxies (R2 = 1.0) for the target variants.
#              Excludes a specific blocklist of known problematic rsIDs.
#

set -euo pipefail

# --- Configuration ---
INPUT_FILE="./data/raw/ldproxy_results.txt"
OUTPUT_FILE="./data/processed/unique_rsid_filtered.txt"
FULL_DETAILS_FILE="./data/processed/filtered_results_details.txt"

# Blocklist: rsIDs to exclude (e.g., known artifacts, multi-allelic issues)
EXCLUDE_RSIDS=("rs149169037" "rs143275498" "rs185526362" "rs76380568" 
               "rs79398237" "rs76255222" "rs141292963" "rs7782915" 
               "rs77986239" "rs6965954" "rs77356730" "rs193214501")

# --- Setup ---
mkdir -p "$(dirname "$OUTPUT_FILE")"

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file $INPUT_FILE not found. Run query_ld_proxy.sh first."
    exit 1
fi

echo "--- Filtering High LD Variants (R2 = 1.0) ---"

# 1. Create a temporary exclusion pattern for grep
# Formats the array into "rs1|rs2|rs3"
EXCLUDE_PATTERN=$(IFS="|"; echo "${EXCLUDE_RSIDS[*]}")

# 2. Process and Filter
# Logic:
#   - grep: Find lines starting with 'rs' (data lines)
#   - awk: Filter where column 7 (R2) is exactly 1.0
#   - grep -v: Exclude the blocklisted IDs
#   - sort | uniq: Remove duplicates

echo "Extracting unique IDs..."
grep -P '^rs\d+\t' "$INPUT_FILE" \
    | awk -F'\t' '$7 == 1.0 {print $1}' \
    | grep -vE "^($EXCLUDE_PATTERN)$" \
    | sort \
    | uniq > "$OUTPUT_FILE"

# 3. Create a detailed file (keeping full line info)
echo "Creating detailed report..."
grep -P '^rs\d+\t' "$INPUT_FILE" \
    | awk -F'\t' '$7 == 1.0' \
    | grep -vE "^($EXCLUDE_PATTERN)\t" \
    > "$FULL_DETAILS_FILE"

# --- Summary ---
COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
echo "Filtering complete."
echo "Found $COUNT unique proxy variants with R2=1.0."
echo "List saved to: $OUTPUT_FILE"
echo "Details saved to: $FULL_DETAILS_FILE"
