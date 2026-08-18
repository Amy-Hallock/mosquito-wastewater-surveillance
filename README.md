# Mosquito Wastewater Surveillance Pipeline

Bioinformatics pipeline for detecting mosquito vector eDNA and insecticide
resistance mutations in municipal wastewater.

## Overview

Traditional mosquito surveillance requires physically trapping and
identifying mosquitoes across a city — slow, labor-intensive, and hard to
scale. This project asks whether municipal wastewater sequencing (the same
approach used for city-wide COVID monitoring) can be extended to detect
mosquito vector species and insecticide-resistance mutations directly from
sewage, without ever catching a mosquito.

## Hypothesis

Deep, untargeted metagenomic sequencing of raw municipal wastewater
contains sufficient genomic depth to:
1. Detect low-abundance environmental DNA (eDNA) from key mosquito vector
   species
2. Track point mutations associated with knockdown resistance (*kdr*) in
   voltage-gated sodium channel genes — specifically the **F1534S** and
   **V1016G** loci

## Target Species

| Species | Role in Study |
|---|---|
| *Culex pipiens* | Positive control — resistance already well-documented in the Boston area |
| *Aedes aegypti* | Emerging vector — testing whether it's detectable in the Boston sewershed at all |
| *Aedes albopictus* | Invasive species — tracking how far resistance has spread in an already-established population |

## Key Concept: Normalized Biomass Index (NBI)

Raw sewage flow fluctuates constantly with rainfall and water use, so raw
sequencing read counts alone don't reflect real population changes — more
rain means more dilution, not fewer mosquitoes. To correct for this, read
counts are normalized against **crAssphage** (`NC_024969.1`), a
bacteriophage shed by humans into wastewater at a stable, predictable rate.

```
Normalized Biomass Index (NBI) = Total Target Vector Reads / Total crAssphage Reads
```

This produces a dilution-independent index that can be compared across
species and over time.

## Pipeline Overview

1. **Infrastructure setup** — cloud compute (GCP/Azure), Conda environment
   with bioinformatics dependencies
2. **Reference genome preparation** — download reference genomes for the
   three target species plus crAssphage from NCBI; build alignment indices
   (bwa-mem2)
3. **Alignment and processing** — align raw wastewater sequencing reads to
   the combined reference database; sort/filter/deduplicate with samtools;
   assess coverage with bedtools
4. **Resistance gene profiling** — call variants at the *kdr* loci
   (F1534S, V1016G) using bcftools; calculate resistance allele frequency
5. **Quantitation and modeling** — calculate NBI per species per sample;
   correlate NBI trends with Boston weather data (temperature, rainfall)
   using Python (pandas, scipy, statsmodels)

## Data Source

Raw sequencing reads: BioProject `PRJNA1247874` (CASPER — Cooperative
Assessment of Sewage Pathogen Emergence and Rise), an actively growing,
multi-city public wastewater metagenomics consortium (not a closed study —
new sites and samples continue to be added).

**Important caveat:** CASPER's sample processing is primarily optimized
for viral RNA capture, with DNA (including host/eukaryotic DNA) captured
only incidentally in some protocol variants. Boston's Deer Island site has
both an RNA-only processing run and a combined RNA+DNA run of the same
physical samples — the RNA+DNA run is the relevant one for this project,
but even that protocol is viral-enrichment-optimized, not designed to
capture eukaryotic genomic DNA like mosquito eDNA. Whether mosquito DNA is
present in detectable quantity in this dataset is an open feasibility
question — see Current Status and Limitations below.

## Tools & Stack

- **Alignment:** bwa-mem2
- **BAM processing:** samtools
- **Variant calling:** bcftools
- **Coverage analysis:** bedtools
- **Analysis:** Python (pandas, numpy, scipy, statsmodels, matplotlib)
- **Environment management:** Conda
- **Compute:** Google Cloud Platform (GCP) / Ubuntu VM

## Repository Structure

```
mosquito-wastewater-surveillance/
├── README.md
├── scripts/
│   ├── calculate_nbi.py         # NBI calculation (raw + genome-length-adjusted), standalone/testable
│   ├── fetch_weather_data.py    # pulls real Boston high/low temp + rainfall (single range)
│   ├── fetch_weather_by_month.py # pulls + splits weather into per-month temp/rainfall files
│   └── get_deer_island_by_collection_date.py # queries CASPER for Deer Island N/S samples by true collection date
├── notebooks/
│   └── nbi_correlation_analysis.ipynb   # NBI + weather correlation demo
├── data/
│   └── weather/                 # per-month temperature + rainfall CSVs (generated, not hand-edited)
│       ├── 2026-03_temperature.csv
│       ├── 2026-03_rainfall.csv
│       ├── 2026-04_temperature.csv
│       ├── 2026-04_rainfall.csv
│       └── ...
└── docs/
    └── pipeline_overview.md     # detailed phase-by-phase breakdown
```

## Current Status

- [x] Pipeline designed (5 phases, full architecture)
- [x] Reference genomes and Conda/cloud environment set up
- [x] NBI calculation script implemented and tested (synthetic data)
- [x] Correlation analysis notebook implemented and tested (synthetic data)
- [x] Real weather data fetch script (Open-Meteo, daily high/low temp + rainfall)
- [x] Weather data split into per-month temperature and rainfall files (March-July)
- [x] NBI calculation extended with genome-length adjustment for cross-species comparison
- [x] Deer Island North/South sample identification by true collection date (vs. SRA release date)
- [ ] **Feasibility check (next step):** confirm mosquito eDNA is actually present in CASPER's
      viral-enrichment-optimized protocol (e.g. via a fast taxonomic classifier like Kraken2)
      before committing to the full alignment pipeline
- [ ] Full alignment pipeline execution on real sequencing data
- [ ] Variant calling on real data
- [ ] Analysis on real NBI values vs. real weather data

## Limitations

- **Protocol feasibility (open question):** CASPER's sample processing is
  optimized for viral RNA/DNA concentration, not eukaryotic genomic DNA
  recovery. It is not yet confirmed that mosquito eDNA is present in this
  dataset at detectable abundance — a fast taxonomic screen is planned as
  the next step before committing further pipeline development to this
  data source.
- Wastewater eDNA reflects relative population trends, not exact mosquito
  counts — per-mosquito DNA shedding rates aren't well characterized
- Detecting a resistance mutation in wastewater doesn't indicate what
  fraction of the local population carries it; environmental DNA from
  multiple sources is mixed together in a single sample
- crAssphage shedding is a reasonable but imperfect stand-in for a truly
  constant human-fecal marker; it can vary somewhat across populations
  and time
- Closely related species (*Aedes aegypti* / *Aedes albopictus*) risk
  confident-but-incorrect read assignment during alignment, a source of
  error distinct from and not caught by MAPQ-based filtering

## Author

Independent project exploring computational genomics and wastewater-based
vector surveillance.
