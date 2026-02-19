#!/bin/bash
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# Script: query_ld_proxy.sh
# Description: Queries the NCI LDlink API (LDproxy) to find variants in high
#              Linkage Disequilibrium (LD) with a target list of rsIDs.
#              Useful for finding proxy variants when the variant of interest
#              is not directly genotyped.
#
# API Documentation: https://ldlink.nci.nih.gov/?tab=apiaccess
#

set -euo pipefail

# --- Configuration ---
# NOTE: You must export LDLINK_API_TOKEN in your environment before running.
# Request a token at: https://ldlink.nci.nih.gov/?tab=apiaccess
API_TOKEN="${LDLINK_API_TOKEN:-}"
BASE_URL="https://ldlink.nci.nih.gov/LDlinkRest/ldproxy"
POPULATION="GBR" # Great Britain
GENOME_BUILD="grch38"
WINDOW_SIZE="500000"
OUTPUT_FILE="./data/raw/ldproxy_results.txt"

# Example List of rsIDs (Targets)
# In production, read this from a file.
TARGET_RSIDS=(
    "rs149169037" "rs143275498" "rs185526362" "rs76380568" 
    "rs79398237" "rs76255222" "rs141292963" "rs7782915" 
    "rs77986239" "rs6965954" "rs77356730" "rs193214501" 
    "rs75991383"
)

# --- Pre-flight Checks ---
if [[ -z "$API_TOKEN" ]]; then
    echo "ERROR: LDLINK_API_TOKEN environment variable is not set."
    echo "Please export your token: export LDLINK_API_TOKEN='your_token_here'"
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"
echo "" > "$OUTPUT_FILE"

echo "--- Starting LDProxy Queries ---"
echo "Target Population: $POPULATION"
echo "Genome Build: $GENOME_BUILD"

# --- Execution ---
for RSID in "${TARGET_RSIDS[@]}"; do
    echo "Querying rsID: $RSID..."
    
    # Perform API Call
    # Using curl with fail flag (-f) to catch HTTP errors
    if response=$(curl -s -f -X GET "${BASE_URL}?var=${RSID}&pop=${POPULATION}&r2_d=r2&window=${WINDOW_SIZE}&genome_build=${GENOME_BUILD}&token=${API_TOKEN}"); then
        echo "$response" >> "$OUTPUT_FILE"
        echo -e "\n" >> "$OUTPUT_FILE" # Separator
    else
        echo "WARNING: Failed to fetch data for $RSID" >&2
    fi
    
    # Be polite to the API
    sleep 1
done

echo "--- Query Complete ---"
echo "Results saved to: $OUTPUT_FILE"
