"""Append a day's rows into a consolidated Parquet dataset, idempotently.

If rows for ``scrape_date`` already exist in the file (e.g. the scrape is
re-run on the same day), they are replaced with the new rows rather than
duplicated, so the dataset always holds at most one observation per
(Date, State-Abbreviation[, Metro-Name]).
"""

from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


STATE_SCHEMA = pa.schema([
    ("State-Name", pa.string()),
    ("State-Abbreviation", pa.string()),
    ("Regular", pa.float64()),
    ("Mid-Grade", pa.float64()),
    ("Premium", pa.float64()),
    ("Diesel", pa.float64()),
    ("Currency", pa.string()),
    ("Unit", pa.string()),
    ("Date", pa.date32()),
])

METRO_SCHEMA = pa.schema([
    ("State-Name", pa.string()),
    ("State-Abbreviation", pa.string()),
    ("Metro-Name", pa.string()),
    ("Regular", pa.float64()),
    ("Mid-Grade", pa.float64()),
    ("Premium", pa.float64()),
    ("Diesel", pa.float64()),
    ("Currency", pa.string()),
    ("Unit", pa.string()),
    ("Date", pa.date32()),
])


def append_day(df, schema, path, scrape_date, sort_keys):
    """Append today's rows to a Parquet dataset, replacing any existing rows for the same date.

    Args:
        df: pandas DataFrame containing this run's rows. Missing schema columns
            are filled with NULL; extra columns are dropped.
        schema: target pyarrow schema.
        path: pathlib.Path-like target for the Parquet file.
        scrape_date: datetime.date — rows with this date are replaced atomically.
        sort_keys: list of (column, "ascending"|"descending") tuples.

    Returns:
        Total row count in the written file.
    """
    expected = [f.name for f in schema]
    for col in expected:
        if col not in df.columns:
            df[col] = None
    df = df[expected]

    new_table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)

    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        existing = pq.read_table(path)
        keep_mask = pc.not_equal(existing["Date"], pa.scalar(scrape_date, type=pa.date32()))
        existing = existing.filter(keep_mask)
        combined = pa.concat_tables([existing, new_table])
    else:
        combined = new_table

    combined = combined.sort_by(sort_keys)
    pq.write_table(combined, path, compression="snappy")
    return combined.num_rows
