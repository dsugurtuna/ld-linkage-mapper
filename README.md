# LD Linkage Mapper

**A toolkit for expanding variant coverage using Linkage Disequilibrium (LD) proxies.**

This repository contains tools to interface with the NCI LDlink API, allowing researchers to find "proxy" variants for SNPs that are not directly genotyped on a specific array (e.g., Affymetrix UK Biobank array). This is a critical step in **Imputation** and **Fine-mapping** workflows.

## 🧬 Scientific Context
In large-scale biobanks, not every genetic variant is directly measured. However, variants close to each other often inherited together (Linkage Disequilibrium). If our target variant is missing, we can look for a "perfect proxy" ($R^2 = 1.0$) that *is* present on the array and use it as a surrogate.

## 📂 Repository Contents

| Script | Role | Description |
| :--- | :--- | :--- |
| `query_ld_proxy.sh` | **API Client** | Queries the **NCI LDlink API** to fetch LD statistics for a list of target rsIDs. Handles authentication and rate limiting. |
| `filter_high_ld_variants.sh` | **Data Filter** | Parses the JSON/Text response from the API to identify perfect proxies ($R^2=1.0$) while filtering out known problematic variants (blocklist). |
| `map_variants_to_participants.py` | **Cohort Mapper** | A high-performance Python script that cross-references the found proxies against the actual participant data file to generate a final availability report. |

## 🚀 Usage

### 1. Setup Environment
You need an API token from NCI LDlink.
```bash
export LDLINK_API_TOKEN="your_token_here"
```

### 2. Fetch Proxies
```bash
./query_ld_proxy.sh
```

### 3. Filter Results
```bash
./filter_high_ld_variants.sh
```

### 4. Map to Cohort
```bash
python3 map_variants_to_participants.py
```

## 🛠️ Technical Highlights
*   **REST API Integration:** Automated querying of external bioinformatics services using `curl`.
*   **Performance Optimization:** Replaced legacy $O(N \times M)$ Bash loops with optimized Python set lookups for mapping variants to large cohorts.
*   **Robust Error Handling:** Includes checks for API tokens, file existence, and HTTP response codes.

---
*Created by [dsugurtuna](https://github.com/dsugurtuna)*
