#!/usr/bin/env python3
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# Script: map_variants_to_participants.py
# Description: Cross-references the list of high-LD proxy variants against
#              a large participant ID file to determine availability.
#              Optimized for performance (replaces O(N*M) bash loop).
#

import sys
import os

# --- Configuration ---
DATA_DIR = "./data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# Inputs
ID_FILE = os.path.join(RAW_DIR, "ukbb_affy_ids.tab") # Large participant file
PRESENT_VARIANTS_FILE = os.path.join(PROCESSED_DIR, "unique_rsid_filtered.txt") # Variants we found on the array

# Outputs
OUTPUT_FILE = os.path.join(PROCESSED_DIR, "participant_rsid_table.txt")

# Target RSIDs (The original list of interest)
TARGET_RSIDS = [
    "rs149169037", "rs143275498", "rs185526362", "rs76380568", "rs79398237", 
    "rs76255222", "rs141292963", "rs7782915", "rs77986239", "rs6965954", 
    "rs77356730", "rs193214501", "rs75991383"
]

def main():
    print("--- Mapping Variants to Participants ---")
    
    # 1. Simulation: Generate dummy input files if they don't exist
    if not os.path.exists(RAW_DIR): os.makedirs(RAW_DIR)
    if not os.path.exists(PROCESSED_DIR): os.makedirs(PROCESSED_DIR)
    
    if not os.path.exists(ID_FILE):
        print(f"Simulating input file: {ID_FILE}")
        with open(ID_FILE, 'w') as f:
            # Header
            f.write("sourceid\trecordid\tsampleid\tindid\tcreate_ts\tupdate_ts\n")
            # Dummy Data
            f.write("UKBB\tREC001\tPART001\tIND001\t2024-01-01\t2024-01-01\n")
            f.write("UKBB\tREC002\tPART002\tIND002\t2024-01-01\t2024-01-01\n")

    if not os.path.exists(PRESENT_VARIANTS_FILE):
        print(f"Simulating present variants file: {PRESENT_VARIANTS_FILE}")
        with open(PRESENT_VARIANTS_FILE, 'w') as f:
            # Assume rs7782915 is present on the array
            f.write("rs7782915\n")

    # 2. Load "Present" Variants into a Set for O(1) lookup
    present_variants = set()
    try:
        with open(PRESENT_VARIANTS_FILE, 'r') as f:
            for line in f:
                rsid = line.strip()
                if rsid:
                    present_variants.add(rsid)
        print(f"Loaded {len(present_variants)} available proxy variants.")
    except FileNotFoundError:
        print(f"Error: {PRESENT_VARIANTS_FILE} not found.")
        sys.exit(1)

    # 3. Process Participants
    # We want to generate a row for every Participant * TargetRSID combination
    # indicating if that TargetRSID (or a proxy) is present.
    
    print(f"Processing participant file: {ID_FILE}")
    
    with open(ID_FILE, 'r') as f_in, open(OUTPUT_FILE, 'w') as f_out:
        # Write Header
        f_out.write("participant_id\trsID\talternative_rsid\tpresent_or_absent\n")
        
        # Skip header of input file
        next(f_in)
        
        count = 0
        for line in f_in:
            parts = line.strip().split('\t')
            if len(parts) < 3: continue
            
            participant_id = parts[2] # sampleid column
            
            # For this participant, check status of all Target RSIDs
            for target_rsid in TARGET_RSIDS:
                # Logic:
                # If the target_rsid itself is in our "present" list -> Present
                # (In a real scenario, we would map Target -> Proxy -> Present. 
                #  Here we simplify based on the user's provided logic which checked 
                #  if the RSID was in the temp file).
                
                if target_rsid in present_variants:
                    status = "present"
                    alt_rsid = target_rsid # Or the proxy that represents it
                else:
                    status = "absent"
                    alt_rsid = "NA"
                
                f_out.write(f"{participant_id}\t{target_rsid}\t{alt_rsid}\t{status}\n")
            
            count += 1
            if count % 1000 == 0:
                print(f"Processed {count} participants...", end='\r')

    print(f"\nDone. Processed {count} participants.")
    print(f"Results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
