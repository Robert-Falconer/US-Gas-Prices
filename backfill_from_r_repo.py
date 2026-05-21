"""Backfill historical US gas price data from the ScrapeUSGasPrices (R) project.

The R-based project https://github.com/gueyenono/ScrapeUSGasPrices recorded
daily city- and state-level AAA gas prices from October 2021 to April 2024.
This script converts those CSVs into this repository's schema and writes them
into ``data/metro-daily-averages/`` and ``data/state-daily-averages/`` so the
time series extends further back than this project's own scrapes.

Mapping notes:
- The R project's per-city tables correspond to this project's "metro" tables;
  both are scraped from the same AAA state-page accordions.
- The R project's per-state tables correspond to this project's "state" tables.
- The R CSVs carry only a state abbreviation, so full state names are restored
  from a lookup table.

Usage::

    python backfill_from_r_repo.py [--r-repo PATH] [--overwrite]

By default the R project is expected to be cloned next to this repository
(``../ScrapeUSGasPrices``). Existing dated CSVs are kept unless ``--overwrite``
is given, so freshly scraped data is never clobbered.
"""

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

CURRENCY = "U.S Dollar"
UNIT = "US Gallon"

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
    "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
    "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

STATE_FIELDNAMES = [
    "State-Name", "State-Abbreviation",
    "Regular", "Mid-Grade", "Premium", "Diesel",
    "Currency", "Unit", "Date",
]
METRO_FIELDNAMES = [
    "State-Name", "State-Abbreviation", "Metro-Name",
    "Regular", "Mid-Grade", "Premium", "Diesel",
    "Currency", "Unit", "Date",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def clean(value):
    """Normalise an R cell value, treating R's NA markers as missing."""
    text = (value or "").strip()
    return "" if text in ("", "NA", "NaN", "N/A", "<NA>") else text


def date_from_name(path):
    match = DATE_RE.search(path.name)
    return match.group(1) if match else None


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def convert_row(row, date, with_metro):
    abbr = clean(row.get("state")).upper()
    if not abbr:
        return None
    record = {
        "State-Name": STATE_NAMES.get(abbr, abbr),
        "State-Abbreviation": abbr,
        "Regular": clean(row.get("regular")),
        "Mid-Grade": clean(row.get("mid")),
        "Premium": clean(row.get("premium")),
        "Diesel": clean(row.get("diesel")),
        "Currency": CURRENCY,
        "Unit": UNIT,
        "Date": date,
    }
    if with_metro:
        metro = clean(row.get("city"))
        if not metro:
            return None
        record["Metro-Name"] = metro
    return record


def convert_file(src, dst, date, fieldnames, with_metro):
    rows = []
    with src.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            record = convert_row(raw, date, with_metro)
            if record is not None:
                rows.append(record)
    if not rows:
        logging.warning("Skipping %s: no usable rows", src.name)
        return False
    write_csv(dst, fieldnames, rows)
    return True


def backfill(src_dir, dst_dir, fieldnames, with_metro, overwrite):
    if not src_dir.is_dir():
        logging.warning("Source folder not found: %s", src_dir)
        return (0, 0, 0)
    written = skipped = failed = 0
    for src in sorted(src_dir.glob("*.csv")):
        date = date_from_name(src)
        if date is None:
            logging.warning("Skipping %s: no date in filename", src.name)
            failed += 1
            continue
        dst = dst_dir / f"{date}.csv"
        if dst.exists() and not overwrite:
            skipped += 1
            continue
        try:
            ok = convert_file(src, dst, date, fieldnames, with_metro)
        except Exception as exc:
            logging.warning("Skipping %s: %s", src.name, exc)
            failed += 1
            continue
        written += 1 if ok else 0
        failed += 0 if ok else 1
    return (written, skipped, failed)


def main(argv=None):
    repo_root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--r-repo", type=Path, default=repo_root.parent / "ScrapeUSGasPrices",
        help="Path to a clone of gueyenono/ScrapeUSGasPrices "
             "(default: ../ScrapeUSGasPrices)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite dated CSVs that already exist (default: keep them)",
    )
    args = parser.parse_args(argv)

    r_repo = args.r_repo.expanduser().resolve()
    if not r_repo.is_dir():
        parser.error(f"R repo not found: {r_repo}")
    logging.info("Backfilling from %s", r_repo)

    results = {
        "state": backfill(
            r_repo / "data" / "state",
            repo_root / "data" / "state-daily-averages",
            STATE_FIELDNAMES, with_metro=False, overwrite=args.overwrite,
        ),
        "metro": backfill(
            r_repo / "data" / "city",
            repo_root / "data" / "metro-daily-averages",
            METRO_FIELDNAMES, with_metro=True, overwrite=args.overwrite,
        ),
    }
    for label, (written, skipped, failed) in results.items():
        logging.info("%s: %d written, %d skipped (already present), %d failed",
                     label, written, skipped, failed)

    return 1 if (results["state"][2] or results["metro"][2]) else 0


if __name__ == "__main__":
    sys.exit(main())
