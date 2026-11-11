########################################################
# Description
########################################################
# script to generate evaluation data used the SEC data.
# We will apply transformations to the company names
########################################################


########################################################
# Imports & Settings
########################################################
import argparse
import random
import re
import string
from pathlib import Path
from typing import Callable

import pandas as pd
########################################################



########################################################
# Fixed
########################################################
LEGAL_SUFFIXES = {
    "CO",
    "COMPANY",
    "CORP",
    "CORPORATION",
    "INC",
    "INCORPORATED",
    "LLC",
    "LLP",
    "LP",
    "LTD",
    "LIMITED",
    "PLC",
}
########################################################


########################################################
# Helpers
########################################################
def normalized_name_key(
        name:str
) -> str:
    """
    produce a simple key used to identify duplicate canonical names
    """
    return re.sub(
        r"[^a-z0-9]+",
        "",
        name.casefold()
    )
########################################################

########################################################
# Transformations
########################################################
def normalize_whitespace(
        name: str,
)-> str:
    """
    Replace repeated whitescpae with a single space
    """
    return " ".join(name.split())
def lowercase(
        name: str,
        rng: random.Random
) -> str:
    return name.lower()

def remove_punctuation(
       name: str,
       rng: random.Random 
) -> str:
    translation = str.maketrans(
        string.punctuation,
        " " *len(string.punctuation)
    )
    return normalize_whitespace(name.translate(translation))

def remove_legal_suffix(
        name: str,
        rng: random.Random,
) -> str:
    """
    Remove a recognized legal suffix from the company name.
    Return the original name when no recognized suffix exists.
    """
    tokens = re.findall(r"[A-Za-z0-9]+", name)
    suffix_removed = False

    while (
        len(tokens) > 1
        and tokens[-1].upper() in LEGAL_SUFFIXES
    ):
        tokens.pop()
        suffix_removed = True

    if not suffix_removed:
        return name

    return " ".join(tokens)

def remove_whitespace(
        name: str,
        rng: random.Random
) -> str:
    """
    concatenante all tokens
    """
    return re.sub(r"\s+", "", name)

def delete_character(
        name: str,
        rng: random.Random        
) -> str:
    """
    Delete one randomly-selected letter/digit
    """
    possible_indices = [
        index for index, character in enumerate(name)
        if character.isalnum()
    ]

    if len(possible_indices) < 4:
        return name
    index = rng.choice(possible_indices)

    return name[:index] + name[index+1:]

def swap_adjacent_characters(
        name: str,
        rng: random.Random        
) -> str:
    """
    swap two adjacent letters/digits
    """
    possible_indices = [
    index for index in range(len(name) - 1)
        if name[index].isalnum()
        and name[index + 1].isalnum()
    ]

    if not possible_indices:
        return name
    
    index = rng.choice(possible_indices)

    characters = list(name)
    characters[index], characters[index+1]= (
        characters[index+1],
        characters[index]
    )
    return "".join(characters)

def substitute_character(
        name: str,
        rng: random.Random        
) -> str:
    """
    replace one letter with another randomly selected letter
    """
    possible_indices = [
    index for index, character in enumerate(name) if character.isalpha()
    ]

    if not possible_indices:
        return name
    index = rng.choice(possible_indices)
    old_character = name[index]

    alphabet = (
        string.ascii_uppercase
        if old_character.isupper()
        else string.ascii_lowercase
    )

    replacements = [
        character for character in alphabet
        if character != old_character
    ]

    replacement = rng.choice(replacements)

    return name[:index]+replacement+name[index+1:]

def remove_token(
        name: str,
        rng: random.Random        
) -> str:
    """
    remove one word from names containing at least three words
    """
    tokens = name.split()

    if len(tokens) < 3:
        return name
    index = rng.randrange(len(tokens))

    del tokens[index]

    return " ".join(tokens)

Transformation = Callable[[str, random.Random], str]

TRANSFORMATIONS: dict[str, Transformation]= {
    "lowercase": lowercase,
    "punctuation_removed": remove_punctuation,
    "legal_suffix_removed": remove_legal_suffix,
    "whitespace_removed": remove_whitespace,
    "character_deleted": delete_character,
    "adjacent_characters_swapped": swap_adjacent_characters,
    "character_substituted": substitute_character,
    "token_removed": remove_token
}
########################################################



########################################################
# Data Generation
########################################################
def generate_variants(
        canonical_name: str,
        variants_per_company: int,
        rng: random.Random
) -> list[tuple[str, str]]:
    """
    Returns (transformation_name, transformed_name) pairs
    """
    transformations = list(TRANSFORMATIONS.items())
    rng.shuffle(transformations)

    variants: list[tuple[str,str]] = []
    seen_names = {canonical_name}

    for transformation_name, transformation in transformations:
        
        transformed_name = transformation(
            canonical_name,
            rng
        )
        
        transformed_name = normalize_whitespace(transformed_name).strip()

        if len( transformed_name) < 2:
            continue
        if transformed_name in seen_names:
            continue

        seen_names.add(transformed_name)

        variants.append(
            (
                transformation_name,
                transformed_name
            )
        )
        if len(variants) >= variants_per_company:
            break

    return variants

def generate_evaluation_data(
        input_path: Path,
        output_path: Path,
        sample_size: int,
        variants_per_company: int,
        test_fraction: float,
        seed: int,
) -> None:
    """
    Generate evaluation data from the canonical names of companies
    """

    rng = random.Random(seed)

    companies = pd.read_csv(
        input_path,
        dtype={"company_id": str}
    )

    required_columns = {
        "company_id",
        "canonical_name"
    }

    missing_columns = required_columns - set(companies.columns)

    if missing_columns:
        raise ValueError(
            f"Input data is missing required columns: {sorted(missing_columns)}"
        )
    companies = companies.dropna(
        subset = ["company_id", "canonical_name"]
    ).copy()

    companies["company_id"] = (
        companies["company_id"].astype(str).str.strip()
    )

    companies["canonical_name"] = (
        companies["canonical_name"].astype(str).map(normalize_whitespace).str.strip()
    )

    companies = companies.drop_duplicates(
        subset=["company_id"]
    )
    # Exclude canonical names shared by multiple company IDs.
    # Those are genuinely ambiguous and should later form a
    # separate challenge set.
    companies["name_key"] = companies[
        "canonical_name"
    ].map(normalized_name_key)

    ambiguous_names = companies["name_key"].duplicated(
        keep=False
    )

    number_ambiguous = int(ambiguous_names.sum())

    companies = companies.loc[
        ~ambiguous_names
    ].copy()

    if len(companies) < 2:
        raise ValueError(
            "At least two unambiguous companies are required"
        )
    
    actual_sample_size = min(
        sample_size,
        len(companies)
    )

    companies = companies.sample(
        n=actual_sample_size,
        random_state=seed,
    ).reset_index(drop=True)

    # split by company before generating variants
    company_ids = companies["company_id"].tolist()
    rng.shuffle(company_ids)

    number_test = max(
        1,
        round(len(company_ids) * test_fraction)
    )

    test_ids = set(company_ids[:number_test])

    rows: list[dict] = []

    for company in companies.itertuples(index=False):
        split = (
            "test" if company.company_id in test_ids else "calibration"
        )

        #inclde the unchanged name as a baseline
        rows.append(
            {
                "query_name": company.canonical_name,
                "expected_company_id": company.company_id,
                "canonical_name": company.canonical_name,
                "transformation": "original",
                "split": split,
                "is_match": True
            }
        )

        variants = generate_variants(
            canonical_name=company.canonical_name,
            variants_per_company=variants_per_company,
            rng=rng
        )

        for transformation_name, query_name in variants:
            rows.append(
                {
                    "query_name": query_name,
                    "expected_company_id": company.company_id,
                    "canonical_name": company.canonical_name,
                    "transformation": transformation_name,
                    "split": split,
                    "is_match": True    
                }
            )
    evaluation_data = pd.DataFrame(rows)

    evaluation_data.insert(
        0,
        "query_id",
        [
            f"q{index:06d}" for index in range(1, len(evaluation_data)+1)
        ]
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    evaluation_data.to_csv(
        output_path,
        index=False
    )

    print(f"Created: {output_path}")
    print(f"Random seed: {seed}")
    print(f"Sampled companies: {actual_sample_size:,}")
    print(f"Excluded ambiguous names: {number_ambiguous:,}")
    print(f"Evaluation queries: {len(evaluation_data):,}")
    print()
    print("Queries by split:")
    print(evaluation_data["split"].value_counts())
    print()
    print("Queries by transformation:")
    print(
        evaluation_data["transformation"].value_counts()
    )
########################################################


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate transformed company-name queries "
            "for matcher evaluation"
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "data/processed/canonical_companies.csv"
        )
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/evaluation/evaluation_queries.csv"
        )
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=1000
    )

    parser.add_argument(
        "--variants-per-company",
        type=int,
        default=4
    )

    parser.add_argument(
        "--test-fraction",
        type=float,
        default=0.2
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42
    )

    args = parser.parse_args()

    if args.sample_size <= 0:
        parser.error(
            "--sample-size must be positive"
        )

    if args.variants_per_company <= 0:
        parser.error(
            "--variants-per-company must be positive"
        )
    if not 0< args.test_fraction < 1:
        parser.error(
            "--test-fraction must be between 0 and 1"
        )
    generate_evaluation_data(
        input_path = args.input,
        output_path = args.output,
        sample_size = args.sample_size,
        variants_per_company= args.variants_per_company,
        test_fraction=args.test_fraction,
        seed=args.seed
    )

if __name__ == "__main__":
    main()