import argparse
import praw
import re
import pandas as pd
import config


def get_stock_list():
    ticker_dict = {}
    filelist = ["input/list1.csv", "input/list2.csv", "input/list3.csv"]
    for file in filelist:
        tl = pd.read_csv(file, skiprows=0, skip_blank_lines=True)
        tl = tl[tl.columns[0]].tolist()
        for ticker in tl:
            ticker_dict[ticker] = 1
    return ticker_dict


def get_prev_tickers():
    prev = open("output/prev.txt", "r")
    prev_tickers = prev.readlines()
    prev_tickers = [x.strip() for x in prev_tickers]
    prev.close()
    return prev_tickers


def get_tickers(sub, stock_list, prev_tickers, score=True, nPosts=-1,
                verbose=0):
    reddit = praw.Reddit(
        client_id=config.api_id,
        client_secret=config.api_secret,
        user_agent=config.api_user_agent,
    )
    weekly_tickers = {}

    # Grab anything that looks like a ticker
    regex_pattern = r'\b([A-Z]+)\b'
    ticker_dict = stock_list
    # Read the blacklist
    blacklist = [x.strip() for x in open('input/blacklist', 'r').readlines()]

    if verbose > 1: print(f'Blacklist: {blacklist}')
    for (i, submission) in enumerate(reddit.subreddit(sub).top("week")):
        if verbose > 0: print(f'Processing submission {i} of {nPosts}')
        if nPosts > 0 and i == nPosts:
            break
        strings = [[submission.title, submission.score, submission.permalink]]
        # This removes all the second and below level comments
        # ATN-2020-12-21: TODO: Is this really what you want?
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            strings.append([comment.body, comment.score, comment.permalink])
        for s in strings:
            for phrase in re.findall(regex_pattern, s[0]):
                if phrase not in blacklist:
                    if verbose > 1: print(phrase)
                    if phrase in ticker_dict:
                        # Reduce string for later printing
                        s[0].replace('\n', ' ')
                        # Count score: number of upvotes for specific comment /
                        # submission
                        score = s[1]

                        if phrase not in weekly_tickers.keys():
                            weekly_tickers[phrase] = [1, score, submission.title, s]
                        else:
                            weekly_tickers[phrase][0] += 1
                            weekly_tickers[phrase][1] += score
                        if verbose > 1:
                           print(f'Found ticker {phrase}, {s}')
                           print(f'Current {phrase} scores: ', weekly_tickers[phrase][0:2])

    if verbose > 1: print(f'Weekly tickers: {weekly_tickers}')

    # Rank the results depending on mentions or score
    if score:
        scoreIndex = 1
    else:
        scoreIndex = 0
    top_tickers = dict(sorted(weekly_tickers.items(), key=lambda x: x[1][scoreIndex], reverse=True)[:5])

    if verbose > 0: print(f'Top tickers: {top_tickers}')

    to_buy = top_tickers
    to_sell = []
    # The sell list if global for now. Not sure there's a point to a per sub
    # one?
    # Removed this for now - if a ticker is at the top, it's prob still a buy?
    # for new in top_tickers:
        # if new not in prev_tickers:
            # to_buy.append(new)
    # for old in prev_tickers:
        # if old not in top_tickers:
            # to_sell.append(old)
    # to_buy = [ticker + '\n' for ticker in to_buy]
    # to_sell = [ticker + '\n' for ticker in to_sell]

    write_to_file(
        'output/' + sub+'.txt',
        map(
           lambda x: f"{x[0]:4s}   m={x[1][0]:6d}, s={x[1][1]:6d} (post: {x[1][2]}, comment: {x[1][3]})\n",
            to_buy.items()
        ),
        map(lambda x: x+"\n", to_sell)
    )
    return to_buy


def write_to_file(file, to_buy, to_sell):
    f = open(file, "w")
    f.write("BUY:\n")
    f.writelines(to_buy)
    f.write("\nSELL:\n")
    f.writelines(to_sell)
    f.close()


def main(
    nPosts=-1,
    score=True,
    subs=["wallstreetbets", "stocks", "investing", "smallstreetbets"],
    verbose=0,
):
    """ Main routine for the wsb_scraper.

    = INPUT VARIABLES:
    nPosts     int: Number of top submissions to consider per sub. Default: all
    score      bool: Use score (true) or mentions. Default: False
    subs       [str]: List of subs to scrape
    verbose    int: Output level. Default: 0
    """
    prev_tickers = get_prev_tickers()
    stock_list = get_stock_list()
    positions = []
    for sub in subs:
        print(f'Retrieving tickers for {sub}')
        # print(sub, stock_list, prev_tickers, score, nPosts, verbose)
        to_buy = get_tickers(sub, stock_list, prev_tickers, score=score,
                             nPosts=nPosts, verbose=verbose)
        for stock in to_buy:
            if stock not in positions:
                positions.append(stock)

    # prev.txt is a global buy list. Could be renamed
    prev = open("output/prev.txt", "w")
    prev.writelines(map(lambda x: x+"\n", positions))
    prev.close()

    # The sell list should be computed here, once all subs are processed
    to_sell = []
    for ticker in prev_tickers:
        if ticker not in positions:
            to_sell.append(ticker)
    sell = open("output/to_sell.txt", "w")
    sell.writelines(map(lambda x: x+"\n", to_sell))
    sell.close()


if __name__ == '__main__':
    # Create and populate argument parser
    parser = argparse.ArgumentParser(prog='compareTrajs.py',description='Compare two trajectories')
    parser.add_argument('-n', '--nPosts', type=int, nargs='?', help='Number of'
                        ' submissions to scrape', default=-1)
    parser.add_argument('-s', '--score', action="store_true", default=False,
                        help='Use the score instead of mentions')
    parser.add_argument('--subs', type=str, nargs='*', metavar="SUB", action='extend',
                        help='Replace list of subs to scrape (default: wsb, stocks, investing, ssb)',
                        default=[])
    parser.add_argument('-v', '--verbose', type=int, nargs='?',
                        help='Different levels of debug output. Default: 0',
                        default=0, const=1, dest='verbose')

    # Read and convert input arguments
    args = parser.parse_args()
    if len(args.subs) == 0:
        args.subs = ["wallstreetbets", "stocks", "investing", "smallstreetbets"]
    main(nPosts=args.nPosts, score=args.score, subs=args.subs, verbose=args.verbose)
