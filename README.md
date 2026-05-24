# US-Gas-Prices

Python scripts that scrape US gas prices.

> 👋 This repository's maintainer is available to hire for US gas prices data-extraction consulting projects. To get a cost estimate, send email to lallyelias87@gmail.com (for projects of any size or complexity).

## Requirements

- [Python 3.10.19+](https://www.python.org/)
- [pip 24.2+](https://github.com/pypa/pip)
- [selenium 4.14.0+](https://github.com/SeleniumHQ/selenium/tree/trunk/py)
- [webdriver-manager 4.0.2+](https://github.com/SergeyPirogov/webdriver_manager)
- [pandas 2.0.3+](https://github.com/pandas-dev/pandas)
- [pyarrow 18.0.0+](https://github.com/apache/arrow)

## Usage

- Clone this repository
```sh
git clone https://github.com/lykmapipo/US-Gas-Prices.git
cd US-Gas-Prices
```

- Install all dependencies

```sh
pip install -r requirements.txt
```

- To scrape [state gas price daily averages](https://gasprices.aaa.com/state-gas-price-averages/), run:

```sh
python scrape_state_daily_averages.py
```

- To scrape [metro gas price daily averages](https://gasprices.aaa.com/state-gas-price-averages/), run:

```sh
python scrape_metro_daily_averages.py
```

## Data

Scraped observations are stored as two consolidated Apache Parquet files:

- `data/state-daily.parquet` — one row per (Date, State).
- `data/metro-daily.parquet` — one row per (Date, State, Metro).

Each scrape run appends that day's rows to the appropriate file; if rows
for the current date already exist (e.g. the workflow is re-run), they
are replaced rather than duplicated. The full history back to
**2021-10-01** is included.

Schemas:

| state-daily.parquet                                                                                  | metro-daily.parquet                                                                                                |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| State-Name, State-Abbreviation, Regular, Mid-Grade, Premium, Diesel, Currency, Unit, Date | State-Name, State-Abbreviation, Metro-Name, Regular, Mid-Grade, Premium, Diesel, Currency, Unit, Date |

### Data Exploration

- With `pandas`:

```python
import pandas as pd

states = pd.read_parquet("data/state-daily.parquet")
metros = pd.read_parquet("data/metro-daily.parquet")

states.info()
```

- With `duckdb` (no read needed — query the file directly):

```python
import duckdb

duckdb.sql("""
    SELECT Date, AVG(Regular) AS avg_regular
    FROM 'data/state-daily.parquet'
    GROUP BY Date
    ORDER BY Date
""").df()
```

- In R (via the `arrow` package):

```r
library(arrow)
states <- read_parquet("data/state-daily.parquet")
```

## Contribute

It will be nice, if you open an issue first so that we can know what is going on, then, fork this repo and push in your ideas. Do not forget to add a bit of test(s) of what value you adding.

## Questions/Contacts

lallyelias87@gmail.com, or open a GitHub issue


## Licence

The MIT License (MIT)

Copyright (c) lykmapipo & Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
