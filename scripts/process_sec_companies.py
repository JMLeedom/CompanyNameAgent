########################################################
# Description
########################################################
# script to process SEC json data
########################################################



########################################################
# Imports & Settings
########################################################
import argparse
import json 
from pathlib import Path

import pandas as pd
########################################################





########################################################
# Data processing
########################################################
def convert_sec_companies(
        input_path: Path,
        output_path:Path,
) -> None:
    with input_path.open("r", encoding = "utf-8") as file:
        raw_data = json.load(file)

    records = list(raw_data.values())

    companies = pd.DataFrame(records)

    required_columns = {"cik_str", "ticker", "title"}
    missing_columns = required_columns - set(companies.columns)

    if missing_columns:
        raise ValueError(
            f"SEC data is missing required columns : {sorted(missing_columns)}"
        )
    companies = companies.rename(
        columns={
            "cik_str": "cik",
            "title": "canonical_name",
        }
    )
    companies["company_id"] = companies["cik"].apply(lambda cik: f"sec_{int(cik):010d}")

    companies["canonical_name"] = (
        companies["canonical_name"].astype(str).str.strip()
    )

    companies = companies[
        ["company_id", "canonical_name", "ticker", "cik"]
    ]


    #some entities may have multiple securities/tickers. matching database should contain only one row per company
    companies = companies.drop_duplicates(
        subset=["company_id"],
        keep = "first"
    )
    companies = companies.sort_values(
        by=["canonical_name","company_id"]
    ).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    companies.to_csv(output_path, index = False)

    print(f"Created {output_path}")
    print(f"Number of unique companies: {len(companies):,}")
    print(companies.head())
########################################################

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert SEC company ticker data to canonical company CSV."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/company_tickers.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/canonical_companies.csv"),
    )

    args = parser.parse_args()
    convert_sec_companies(args.input, args.output)


if __name__ == "__main__":
    main()