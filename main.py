import argparse
import config
import json
import os
import pandas as pd
import praw
import re
import sys


def get_stock_list(inputDir):
    ticker_dict = {}
    filelist = [
        f'{inputDir}/{file}' for file in ["list1.csv", "list2.csv", "list3.csv"]
    ]

    generic_words = [
        x.strip() for x in open(f'{inputDir}/generic', 'r').readlines()
    ]
    for file in filelist:
        tl = pd.read_csv(file, skiprows=0, skip_blank_lines=True)
        tickerList = tl[tl.columns[0]].tolist()
        companyList = tl[tl.columns[1]].tolist()
        for (ticker, company) in zip(tickerList, companyList):
            # First, try to isolate > 3 char words
            ticker_dict[ticker] = [
                x for x in company.strip().split(' ')
                if x.lower() not in generic_words and len(x.lower()) > 3
            ]

            # If there isn't any, accept all
            if len(ticker_dict[ticker]) == 0:
                ticker_dict[ticker] = [
                    x for x in company.strip().split(' ')
                    if x.lower() not in generic_words
                ]

    return ticker_dict


def get_prev_tickers(filename):
    if os.path.isfile(filename):
        with open(f"{filename}", "r") as prev:
            prev_tickers = json.load(prev)
    else:
        prev_tickers = []

    return prev_tickers


def get_tickers(sub, stock_list, prev_tickers, metric='m', nPosts=-1,
                top=5, time='week', inputDir='./input', outputDir='./output',
                verbose=0):
    reddit = praw.Reddit(
        client_id=config.api_id,
        client_secret=config.api_secret,
        user_agent=config.api_user_agent,
    )
    weekly_tickers = {}

    # Grab anything that looks like a ticker
    regex_pattern = r'\b([A-Z]{1,6})\b'
    ticker_dict = stock_list
    # Read the blacklist and graylist
    blacklist = [
        x.strip() for x in open(f'{inputDir}/blacklist', 'r').readlines()
    ]
    graylist = {}
    for x in open(f'{inputDir}/graylist', 'r').readlines():
        entry = x.strip('\n').split(' ', maxsplit=1)
        graylist[entry[0]] = []
        if len(entry) > 1:
            graylist[entry[0]] = [s.strip() for s in entry[1].split(',')]

    if verbose > 1:
        print(f"Blacklist: {blacklist}")
        print(f"Graylist: {graylist}")

    # Go through top submissions of the week
    # ATN-2020-12-21: TODO: Make this an input - could want the top of the day
    # or something else
    for (i, submission) in enumerate(reddit.subreddit(sub).top(f"{time}")):
        if verbose > 0:
            print(f'Processing submission {i} of {nPosts}', flush=True)
        if nPosts > 0 and i == nPosts:
            break

        # Store title + body, score, and link
        strings = [[submission.title + submission.selftext,
                    submission.score, submission.permalink]]

        # This removes all the second and below level comments
        # ATN-2020-12-21: TODO: Is this really what you want?
        submission.comments.replace_more(limit=0)

        # Go through the comments
        for comment in submission.comments.list():
            # Keep the body, score, and link
            strings.append([comment.body, comment.score, comment.permalink])

        # Go through all the strings
        for s in strings:
            for phrase in re.findall(regex_pattern, s[0]):

                # If blacklisted, move on
                if phrase in blacklist:
                    if verbose > 1:
                        print(f'Blacklisted: {phrase}')
                    continue
                # If phrase not in ticker_dict, move on
                if phrase not in ticker_dict:
                    if verbose > 1:
                        print(f'Not a ticker: {phrase}')
                    continue
                # If phrase in graylist, see if the keywords are mentioned
                if (phrase in graylist or len(phrase) == 1):
                    # The graylist has precedence
                    kw = graylist.get(phrase, [])
                    if len(kw) == 0:
                        kw = ticker_dict[phrase]
                    # Check whether any of the
                    if not any([f' {x.lower()} ' in f' {s[0].lower()} '
                                for x in kw]):
                        if verbose > 1:
                            print(f'Graylisted: {phrase} ; s: {s}')
                        continue
                    else:
                        if verbose > 1:
                            print(f'Graylist member, mentioned in text:'
                                  f' {phrase} ; s: {s}')
                            print(f'keywords: {kw}')
                            print('list: '
                                  f'{[x.lower() in s[0].lower() for x in kw]}')

                # Reduce string for later printing
                s[0].replace('\n', ' ')

                # New ticker
                newTicker = {
                    'm': 1,
                    's': s[1],
                    'topSubmission': {
                        'sub': sub,
                        'title': submission.title,
                        's': s[1],
                        'link': s[2],
                        'text': s[0]
                    },
                    'name': phrase
                }
                add_ticker(weekly_tickers, newTicker, verbose)

    if verbose > 1:
        print(f'Weekly tickers: {weekly_tickers}')

    # Rank the results depending on mentions or score. We look into x[1]
    # because x is the tuple (key, value)
    weekly_tickers = dict(
        sorted(weekly_tickers.items(), key=lambda x: x[1][metric],
               reverse=True)
    )
    top_tickers = dict(
        sorted(weekly_tickers.items(), key=lambda x: x[1][metric],
               reverse=True)[0:min(top, len(weekly_tickers))]
    )

    if verbose > 0:
        print(f'Top tickers: {top_tickers.keys()}')

    # Removed from upstream: - per-ub sell list ; not buying items that were
    # already on the buy list

    # Write sub-specific file
    write_to_file(
        [f'{outputDir}/{sub}{suf}.json' for suf in ['', '_all']],
        [top_tickers, weekly_tickers],
    )
    return top_tickers


def write_to_file(filenames, ticker_dicts):

    if isinstance(ticker_dicts, dict):
        ticker_dicts = [ticker_dicts]

    if isinstance(filenames, str):
        filenames = [filenames]

    if len(filenames) != len(ticker_dicts):
        raise Exception(f'Input Error: filenames has len {len(filenames)},'
                        f' ticker_dicts has len {len(ticker_dicts)}.')

    # Write top & keep all stats as well
    for (tickers, filename) in zip(ticker_dicts, filenames):
        with open(filename, "w") as f:
            json.dump(tickers, f, indent=2, sort_keys=False)
            # f.write("BUY:\n")
            # f.writelines(
                # map(
                    # lambda x: f"{x[0]:4s}   m={x[1][0]:6d}, s={x[1][1]:6d}"
                              # f" (post: {x[1][2]}, comment: {x[1][3]})\n",
                    # tickers.items()
                # ),
            # )


def add_ticker(destDict, tickerDict, verbose=0):

    ticker = tickerDict['name']
    if ticker not in destDict:
        destDict[ticker] = tickerDict

    else:
        # Add mentions
        destDict[ticker]['m'] += tickerDict['m']
        # Add score
        destDict[ticker]['s'] += tickerDict['s']

        # Keep highest score submission
        if (destDict[ticker]['topSubmission']['s']
                < tickerDict['topSubmission']['s']):
            destDict[ticker]['topSubmission'] = tickerDict['topSubmission']

        if verbose > 1:
            print(f"Found ticker {ticker} for the"
                    f" {destDict[ticker]['s']}th time"
                    f"{tickerDict['topSubmission']}")


def main(
    nPosts=-1,
    top=5,
    score=True,
    subs=["wallstreetbets", "stocks", "investing", "smallstreetbets"],
    time='week',
    prevFile='./input/to_buy_prev.json',
    inputDir='./input',
    outputDir='./output',
    verbose=0,
):
    """ Main routine for the wsb_scraper.

    = INPUT VARIABLES:
    nPosts     int: Number of top submissions to consider per sub. Default: all
    score      bool: Use score (true) or mentions. Default: False
    subs       [str]: List of subs to scrape
    verbose    int: Output level. Default: 0
    """
    # --- Set runs up
    # Make output dir
    print(outputDir)
    if not os.path.isdir(f'{outputDir}'):
        os.makedirs(outputDir)
    prev_tickers = get_prev_tickers(prevFile)
    stock_list = get_stock_list(inputDir)
    # Set scoring system
    if score:
        metric = 's'
    else:
        metric = 'm'

    # --- Go through each sub
    positions = {}
    for sub in subs:
        if verbose > -1:
            print(f'Retrieving tickers for {sub}', flush=True)
        to_buy = get_tickers(sub, stock_list, prev_tickers, metric=metric,
                             nPosts=nPosts, top=top, time=time,
                             inputDir=inputDir, outputDir=outputDir,
                             verbose=verbose)

        # Add to the running list
        for stock in to_buy:
            add_ticker(positions, to_buy[stock])

    print('💵  🚀  DONE!!  🚀  💵')

    # --- Write global buy list
    positions = dict(sorted(positions.items(),
                            key=lambda x: x[1][metric],
                            reverse=True))
    write_to_file(f"{outputDir}/to_buy.json", positions)

    # The sell list should be computed here, once all subs are processed
    to_sell = []
    for ticker in prev_tickers:
        if ticker not in positions:
            to_sell.append(ticker)
    sell = open(f"{outputDir}/to_sell.json", "w")
    sell.writelines(map(lambda x: x+"\n", to_sell))
    sell.close()


if __name__ == '__main__':
    # Create and populate argument parser
    parser = argparse.ArgumentParser(prog='wsb_scraper')
    parser.add_argument('-n', '--nPosts', type=int, nargs='?', help='Number of'
                        ' submissions to scrape', default=-1)
    parser.add_argument('-t', '--top', type=int, nargs='?', help='Top X number'
                        ' of tickers are kept. Default: 5', default=5)
    parser.add_argument('-s', '--score', action="store_true", default=False,
                        help='Use the score instead of mentions')
    parser.add_argument('--subs', type=str, nargs='*', metavar="SUB",
                        action='extend', help='Replace list of subs to scrape'
                        ' (default: wsb, stocks, investing, ssb)', default=[])
    parser.add_argument('-ti', '--time', type=str, nargs='?', help='Time'
                        ' filter for top posts. Can be one of: all, day, hour,'
                        ' month, week, year (default: week).', default='week')
    parser.add_argument('-p', '--prev', type=str, nargs='?', help='File'
                        ' to use as previous buy list. Default:'
                        ' ./input/to_buy_prev.json',
                        default='./input/to_buy_prev.json')
    parser.add_argument('-i', '--input', type=str, nargs='?', help='Input'
                        ' directory. Default: ./input', default='./input')
    parser.add_argument('-o', '--output', type=str, nargs='?', help='Output'
                        ' directory. Default: ./output', default='./output')
    parser.add_argument('-v', '--verbose', type=int, nargs='?',
                        help='Different levels of debug output. Default: 0'
                        ' -1 for complete silence', default=0, const=1,
                        dest='verbose')

    # Read and convert input arguments
    args = parser.parse_args()
    if len(args.subs) == 0:
        args.subs = ["wallstreetbets", "stocks", "investing",
                     "smallstreetbets"]
    main(
        nPosts=args.nPosts,
        top=args.top,
        score=args.score,
        subs=args.subs,
        time=args.time,
        prevFile=args.prev,
        inputDir=args.input,
        outputDir=args.output,
        verbose=args.verbose,
    )
