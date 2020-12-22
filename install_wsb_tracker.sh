#!/usr/bin/env bash
python -m venv wsb_scraper_venv
source wsb_scraper_venv/bin/activate
pip install praw
pip install pandas
deactivate
