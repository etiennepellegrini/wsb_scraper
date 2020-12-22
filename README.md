# wsb_scraper
scrapes WSB for top 5 stocks each week. Keeps track of previous week's top 5. If a stock stays in the top 5, we hold, If it leaves the top 5, we sell. If a stock enters the top 5, we buy. 


Files:

list1.csv, list2.csv, list3.csv: CSV files for list of tickers

prev: previous week's top 5 stocks

main: central python script

# Instructions

- Create login info:
    - Copy the `config_template.py` to `config,py`
    - Follow the intructions to retrieve an `api_id` and `api_secret` ; update
        `api_user_agent` as well

- Optional: Create & activate venv
    - `python -m venv wsb_scraper_venv`
    - `source wsb_scraper_venv/bin/activate`

- Install dependencies
    - `pip install praw`
    - `pip install pandas`

- Run & profit :moneybag: :rocket:
    - `python main,py [options]`
    or
    - `./run_wsb_scraper.sh [options]`
    The second option activates the `venv` for you

Use `./run_wsb_scraper.sh -h` to see the available options and their defaults.
