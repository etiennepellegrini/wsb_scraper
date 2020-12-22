# wsb_scraper
scrapes WSB for top 5 stocks each week. Keeps track of previous week's top 5. If a stock stays in the top 5, we hold, If it leaves the top 5, we sell. If a stock enters the top 5, we buy.


Files:

list1.csv, list2.csv, list3.csv: CSV files for list of tickers

prev: previous week's top 5 stocks

main: central python script

# Instructions

## Usage

- Create login info:
    - Copy the `config_template.py` to `config,py`
    - Follow the intructions to retrieve an `api_id` and `api_secret` ; update
        `api_user_agent` as well

- Optional: Create & activate venv
```bash
python -m venv wsb_scraper_venv
source wsb_scraper_venv/bin/activate
```

- Install dependencies
```bash
pip install praw
pip install pandas
```

- Run & profit :moneybag: :rocket:
    - `python main,py [options] > scraper.log 2>&1 &`
    or
    - `./run_wsb_scraper.sh [options] > scraper.log 2>&1 &`
    - The second option activates the `venv` for you

Use `./run_wsb_scraper.sh -h` to see the available options and their defaults.

## Inputs

### Graylist

List ambiguous tickers, and the keywords to check for in the body of the posts
(comma-separated list)

### Blacklist

List strings that are automatically excluded (for some strings like `WSB`,
graylisting them would waste time when probability of actual ticker is very low)

### generic

Contains list of words too generic to act as keywords
