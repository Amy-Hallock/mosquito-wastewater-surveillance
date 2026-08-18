# Pipeline Overview

Detailed phase-by-phase breakdown of the computational pipeline.

## Phase 1: Infrastructure and Cloud Environment Setup

**Storage & Compute (GCP/Azure)**
- Fetch raw sequencing reads (BioProject `PRJNA1247874`, CASPER dataset)
  directly to cloud storage
- Provision a high-CPU/RAM compute instance (32+ vCPUs, 128GB+ RAM) to
  handle large-scale metagenomic alignment

**Environment Management (Conda)**
- Isolated environment containing all bioinformatics dependencies
  (bwa-mem2, samtools, bcftools, bedtools) to ensure reproducibility

## Phase 2: Reference Genome and Index Preparation (NCBI)

**Reference Genome Acquisition**
- Fetch reference assemblies for target vectors (*Culex pipiens*,
  *Aedes aegypti*, *Aedes albopictus*) from NCBI Datasets
- Fetch crAssphage reference (`NC_024969.1` / `NC_024711.1`) from NCBI
  GenBank as the internal normalization control
- Merge into a single composite FASTA reference database for
  simultaneous competitive read mapping

**Index Building**
- Build BWT/FM-index structures with bwa-mem2 for fast alignment across
  gigabase-scale references
- Build coordinate lookup indices for the voltage-gated sodium channel
  (VGSC) gene regions harboring the *kdr* loci, to enable targeted
  downstream variant querying

## Phase 3: Alignment and Sequence Data Processing (BAM Pipeline)

**Metagenomic Reference Mapping**
- Align reads using a seed-and-extend approach
- Assign low mapping quality scores (MAPQ < 30) to non-unique/ambiguous
  reads that align to more than one species, to reduce false-positive
  quantitation

**BAM Stream Processing**
- Convert/sort raw alignment output into BAM format with samtools
- Filter unmapped reads, low-confidence alignments (MAPQ < 30), and PCR
  duplicates
- Build coordinate-indexed BAM files for fast targeted region lookup

**Alignment Metric Extraction**
- Compute coverage breadth (% of genome covered) and depth
  (fold-coverage) with bedtools to distinguish real eDNA signal from
  sequencing noise

## Phase 4: Resistance Gene Profiling and Variant Calling (*kdr* Loci)

**Targeted Variant Calling**
- Extract alignment slices spanning the VGSC gene regions
- Generate base-by-base allele frequency and read-depth pileups at the
  F1534S and V1016G positions using `bcftools mpileup`

**Low-Abundance SNP Profiling**
- Call variants with parameters optimized for low-frequency detection in
  heterogeneous metagenomic samples
- Calculate Resistance Allele Frequency (RAF) — the ratio of
  mutant-to-wildtype read depth at each *kdr* locus

## Phase 5: Relative Quantitation and Environmental Modeling

**Data Normalization**
- Process read count tables in Python (pandas/numpy) to calculate the
  Normalized Biomass Index (NBI) for each species:

  ```
  NBI = Total Target Vector Reads / Total crAssphage Reads
  ```

- This removes dilution bias caused by storm flow and municipal water
  use fluctuations

**Meteorological Correlation and Time-Series Modeling**
- Merge temporal NBI values (March–October) with daily Boston weather
  data (temperature, rainfall, thaw cycles)
- Run Pearson/Spearman correlation testing and lag-response regression
  (Python: scipy, statsmodels) to evaluate how microclimate shifts and
  precipitation events drive vector emergence and eDNA shedding
