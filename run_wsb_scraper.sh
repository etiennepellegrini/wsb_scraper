#!/usr/bin/env bash
source wsb_scraper_venv/bin/activate >& 'tt'
which -a python
python main.py "$@" >& 'tt2'
