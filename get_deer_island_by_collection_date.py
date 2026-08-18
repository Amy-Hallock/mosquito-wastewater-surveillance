"""
get_deer_island_by_collection_date.py

Pulls Deer Island (Boston) run metadata from BioProject PRJNA1247874, and
resolves the TRUE sample collection date (not the SRA release/load date).

Why this matters:
  - The SRA "runinfo" table (Run Selector export) contains database
    housekeeping dates like ReleaseDate/LoadDate — these reflect when the
    data was POSTED to SRA, not when the sample was actually collected.
  - The real collection date lives in the BioSample record, as an
    attribute typically named "collection_date".
  - For this project, we need the real collection date to correctly match
    each sample against the weather conditions on the day it was taken.

Workflow:
  1. Fetch the run-level table (Run, BioSample accession, ReleaseDate, etc.)
  2. Filter for Deer Island North/South
  3. For each BioSample, fetch its attributes and extract collection_date
  4. Output a clean table with BOTH dates side by side, labeled clearly,
     plus a North/South split organized by TRUE collection date
"""

import time
import requests
import pandas as pd
from io import StringIO
import xml.etree.ElementTree as ET

BIOPROJECT = "PRJNA1247874"


def fetch_runinfo(bioproject: str) -> pd.DataFrame:
    """Fetch the run-level metadata table (includes ReleaseDate, LoadDate)."""
    url = "https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo"
    params = {"acc": bioproject}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))


def filter_deer_island(df: pd.DataFrame) -> pd.DataFrame:
    """Filter the run table down to Deer Island (Boston) samples only."""
    text_cols = df.select_dtypes(include="object").columns
    mask = df[text_cols].apply(
        lambda col: col.str.contains("Deer Island", case=False, na=False)
    ).any(axis=1)
    return df[mask].copy()


def fetch_biosample_collection_date(biosample_id: str) -> str:
    """
    Query NCBI's efetch endpoint for a single BioSample and extract the
    'collection_date' attribute — the TRUE sample collection date.
    """
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "biosample", "id": biosample_id, "rettype": "xml"}
    response = requests.get(url, params=params)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    for attr in root.iter("Attribute"):
        if attr.get("attribute_name", "").lower() in ("collection_date", "collection date"):
            return attr.text
    return None  # not found — some samples may not have it populated


def add_true_collection_dates(deer_island_df: pd.DataFrame, biosample_col: str) -> pd.DataFrame:
    """
    Loop through each BioSample accession and fetch its true collection
    date, adding it as a new column. Pauses briefly between requests to
    stay within NCBI's rate limits.
    """
    collection_dates = []
    for biosample_id in deer_island_df[biosample_col]:
        try:
            date = fetch_biosample_collection_date(biosample_id)
        except Exception as e:
            print(f"  Warning: failed to fetch {biosample_id}: {e}")
            date = None
        collection_dates.append(date)
        time.sleep(0.4)  # be polite to NCBI's servers

    deer_island_df["true_collection_date"] = collection_dates
    return deer_island_df


def label_site(deer_island_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'site' column labeling each row as 'North' or 'South' based on
    which text column mentions it. Prints anything that couldn't be
    labeled so it can be checked by hand.
    """
    text_cols = deer_island_df.select_dtypes(include="object").columns

    def find_site(row):
        row_text = " ".join(str(v) for v in row[text_cols].values)
        if "north" in row_text.lower():
            return "North"
        elif "south" in row_text.lower():
            return "South"
        return "Unknown"

    deer_island_df["site"] = deer_island_df.apply(find_site, axis=1)

    unknown = deer_island_df[deer_island_df["site"] == "Unknown"]
    if len(unknown) > 0:
        print(f"  Warning: {len(unknown)} rows could not be labeled North/South — check manually")

    return deer_island_df


def pair_north_south_by_date(deer_island_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reorganize so each row represents one collection DATE, with the
    matching North and South sample info side by side. If a date has
    more than one run for a site (e.g. resequencing), all are joined
    with a semicolon so nothing is silently dropped.
    """
    north = deer_island_df[deer_island_df["site"] == "North"]
    south = deer_island_df[deer_island_df["site"] == "South"]

    def collapse(df, prefix):
        grouped = df.groupby("true_collection_date").agg({
            "Run": lambda x: ";".join(x.astype(str)),
            "BioSample": lambda x: ";".join(x.astype(str)),
        })
        grouped.columns = [f"{prefix}_{c}" for c in grouped.columns]
        return grouped

    north_grouped = collapse(north, "north")
    south_grouped = collapse(south, "south")

    paired = north_grouped.join(south_grouped, how="outer").reset_index()
    paired = paired.rename(columns={"true_collection_date": "collection_date"})
    paired = paired.sort_values("collection_date")

    # Flag dates missing one side, since that affects the North vs. South comparison
    paired["complete_pair"] = paired["north_Run"].notna() & paired["south_Run"].notna()
    missing = paired[~paired["complete_pair"]]
    if len(missing) > 0:
        print(f"  Note: {len(missing)} dates have only one site (North or South), not both")

    return paired


if __name__ == "__main__":
    print("Fetching full run table...")
    runinfo = fetch_runinfo(BIOPROJECT)

    print("Filtering for Deer Island...")
    deer_island = filter_deer_island(runinfo)
    print(f"Found {len(deer_island)} Deer Island runs")
    print("Columns available:", deer_island.columns.tolist())

    # NOTE: adjust "BioSample" below if the actual column name differs —
    # print(deer_island.columns.tolist()) above will show the real name
    print("\nFetching TRUE collection dates from BioSample records...")
    deer_island = add_true_collection_dates(deer_island, biosample_col="BioSample")

    # Keep both dates clearly labeled so nothing gets confused later
    output_cols = ["Run", "BioSample", "true_collection_date", "ReleaseDate", "LoadDate"]
    output_cols = [c for c in output_cols if c in deer_island.columns]
    result = deer_island[output_cols]

    result.to_csv("deer_island_runs_with_true_dates.csv", index=False)
    print("\nSaved: deer_island_runs_with_true_dates.csv")
    print(result.head())

    print("\nLabeling North vs. South...")
    deer_island = label_site(deer_island)

    print("Pairing North and South samples by collection date...")
    paired = pair_north_south_by_date(deer_island)

    paired.to_csv("deer_island_north_south_by_date.csv", index=False)
    print("\nSaved: deer_island_north_south_by_date.csv")
    print(paired.head())
