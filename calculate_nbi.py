"""
calculate_nbi.py

Calculates the Normalized Biomass Index (NBI) for target mosquito vector
species from wastewater sequencing read counts, using crAssphage as an
endogenous internal control to correct for sewage dilution.

Two versions are provided:

1. Raw NBI  -  NBI = Target Reads / crAssphage Reads
   Valid for tracking a SINGLE species' trend over time, since genome
   length is constant within a species and cancels out across samples.

2. Adjusted NBI (genome-length-normalized)  -  same logic as RPKM in
   RNA-seq. Larger genomes attract proportionally more reads at the same
   true abundance, purely due to genome size, so raw NBI is NOT valid for
   comparing across species with different genome sizes. Adjusted NBI
   corrects for this by converting read counts to "read density"
   (reads per kilobase of genome) before taking the ratio:

   Adjusted NBI = (Target Reads / Target Genome Length in kb)
                  / (crAssphage Reads / crAssphage Genome Length in kb)
"""

import pandas as pd

# Approximate reference genome lengths (kb). Update these to match the
# exact reference assemblies used in the alignment step (Phase 2/3),
# since assembly versions can differ slightly in reported length.
GENOME_LENGTHS_KB = {
    "culex": 579_000,
    "aegypti": 1_200_000,
    "albopictus": 1_200_000,  # update to match the specific reference used
    "crassphage": 97,
}


def calculate_nbi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add raw NBI columns to a DataFrame of read counts.

    Use for within-species trends over time (e.g. Culex NBI in April vs.
    Culex NBI in July) — NOT valid for comparing NBI across species.

    Expects columns: culex_reads, aegypti_reads, albopictus_reads, crassphage_reads
    Returns a copy of df with NBI_culex, NBI_aegypti, NBI_albopictus columns added.
    """
    df = df.copy()
    df["NBI_culex"] = df["culex_reads"] / df["crassphage_reads"]
    df["NBI_aegypti"] = df["aegypti_reads"] / df["crassphage_reads"]
    df["NBI_albopictus"] = df["albopictus_reads"] / df["crassphage_reads"]
    return df


def calculate_adjusted_nbi(df: pd.DataFrame, genome_lengths_kb: dict = GENOME_LENGTHS_KB) -> pd.DataFrame:
    """
    Add genome-length-adjusted NBI columns to a DataFrame of read counts.

    Use for comparing NBI ACROSS species (e.g. is Culex more abundant
    than Aedes aegypti on the same date), since this corrects for the
    fact that larger genomes generate more reads at the same true
    abundance, purely due to genome size.

    Expects columns: culex_reads, aegypti_reads, albopictus_reads, crassphage_reads
    Returns a copy of df with adjusted_NBI_culex, adjusted_NBI_aegypti,
    adjusted_NBI_albopictus columns added.
    """
    df = df.copy()

    crassphage_density = df["crassphage_reads"] / genome_lengths_kb["crassphage"]

    culex_density = df["culex_reads"] / genome_lengths_kb["culex"]
    aegypti_density = df["aegypti_reads"] / genome_lengths_kb["aegypti"]
    albopictus_density = df["albopictus_reads"] / genome_lengths_kb["albopictus"]

    df["adjusted_NBI_culex"] = culex_density / crassphage_density
    df["adjusted_NBI_aegypti"] = aegypti_density / crassphage_density
    df["adjusted_NBI_albopictus"] = albopictus_density / crassphage_density

    return df


if __name__ == "__main__":
    # Example / synthetic sample data — replace with real Phase 3 alignment
    # output (read counts per sample per species) once available.
    data = {
        "sample_date": ["2026-04-01", "2026-05-01", "2026-06-01"],
        "culex_reads": [120, 340, 560],
        "aegypti_reads": [5, 12, 30],
        "albopictus_reads": [40, 90, 150],
        "crassphage_reads": [10000, 12000, 9500],
    }
    df = pd.DataFrame(data)

    print("Raw NBI (use for within-species trends over time):")
    raw_result = calculate_nbi(df)
    print(raw_result)

    print("\nAdjusted NBI (use for cross-species comparison):")
    adjusted_result = calculate_adjusted_nbi(df)
    print(adjusted_result)
