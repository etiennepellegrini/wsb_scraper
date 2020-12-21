# wsb_scraper
Scrapes WSB and other investing subreddits for top stocks each week, by mentions
or score.

# Instructions

## Installation

- Clone this repo wherever you'd like.

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
pip install robin-stocks
```

## Run & profit :moneybag: :rocket:

- Use `./run_wsb_scraper.sh -h` to see the available options and their defaults.

- Single run:
    - `python main,py [options] > scraper.log 2>&1 &`
    or
    - `./run_wsb_scraper.sh [options] > scraper.log 2>&1 &`
        - ==> activates the `venv` for you

- Multi-run / historical data:
    - `runAll.sh` starts 6 runs: day, week, month, for both scores and mentions,
        and saves the output to `output/<date>`
    - By default, `runAll.sh`:
        - tries to load
            `output/<yesterday>/<mention|score>/<day|week|month>/to_buy.txt`
            as the previous buy list
    - All the other options (at their default) can be overwritten from the
        command line
    
```bash
./runAll.sh [options] > runAll_$(date +"%Y%m%dT%H%M").log 2>&1 &
```

# "Doc"

## Input Files

### Graylist

List ambiguous tickers, and the keywords to check for in the body of the posts
(comma-separated list)

### Blacklist

List strings that are automatically excluded (for some strings like `WSB`,
graylisting them would waste time when probability of actual ticker is very low)

### generic

Contains list of words too generic to act as keywords when checking the graylist

## Output Files

### [subName].txt

Contains the top `n` (default 5) tickers for the specified sub

### to_buy.txt

Contains the merged list from all considered subs

### to_sell.txt

Messed up at the moment. Should contain tickers that dropped in mentions
