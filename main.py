import argparse
import pandas as pd
import praw
import re
import config


def get_stock_list():
    ticker_dict = {}
    filelist = ["input/list1.csv", "input/list2.csv", "input/list3.csv"]
    generic_words = ["inc", "group", "company"]
    for file in filelist:
        tl = pd.read_csv(file, skiprows=0, skip_blank_lines=True)
        tickerList = tl[tl.columns[0]].tolist()
        companyList = tl[tl.columns[1]].tolist()
        for (ticker, company) in zip(tickerList, companyList):
            ticker_dict[ticker] = [x for x in company.strip().split(' ')
                                   if x.lower() not in generic_words]
    return ticker_dict


def get_prev_tickers():
    prev = open("output/prev.txt", "r")
    prev_tickers = prev.readlines()
    prev_tickers = [x.strip() for x in prev_tickers]
    prev.close()
    return prev_tickers


def get_tickers(sub, stock_list, prev_tickers, score=True, nPosts=-1,
                top=5, verbose=0):
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
    blacklist = [x.strip() for x in open('input/blacklist', 'r').readlines()]
    graylist = {}
    for x in open('input/graylist', 'r').readlines():
        entry = x.strip('\n').split(' ')
        graylist[entry[0]] = entry[1:]

    if verbose > 1:
        print(f"Blacklist: {blacklist}")
        print(f"Graylist: {graylist}")

    # Go through top submissions of the week
    # ATN-2020-12-21: TODO: Make this an input - could want the top of the day
    # or something else
    for (i, submission) in enumerate(reddit.subreddit(sub).top("week")):
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
                    kw = graylist.get(phrase, []) + ticker_dict[phrase]
                    if not any([' ' + x.lower() + ' ' in s[0].lower()
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
                if phrase not in weekly_tickers.keys():
                    if verbose > 0:
                        print(f'New ticker found: {phrase}, s={[1]}')
                    weekly_tickers[phrase] = [1, s[1], submission.title, s]
                else:
                    weekly_tickers[phrase][0] += 1
                    weekly_tickers[phrase][1] += s[1]
                if verbose > 1:
                    print(f'Found ticker {phrase} for the'
                          f' {weekly_tickers[phrase][0]}th time, {s}')
                    print(f'Current {phrase} scores: ',
                          weekly_tickers[phrase][0:2])

    if verbose > 1:
        print(f'Weekly tickers: {weekly_tickers}')

    # Rank the results depending on mentions or score
    if score:
        scoreIndex = 1
    else:
        scoreIndex = 0
    top_tickers = dict(sorted(weekly_tickers.items(),
                              key=lambda x: x[1][scoreIndex],
                              reverse=True)[:min(top, len(weekly_tickers))])

    if verbose > 0:
        print(f'Top tickers: {top_tickers}')

    to_buy = top_tickers
    to_sell = []

    # Removed from upstream: - per-ub sell list ; not buying items that were
    # already on the buy list

    # Write sub-specific file
    write_to_file(
        'output/' + sub+'.txt',
        map(
            lambda x: f"{x[0]:4s}   m={x[1][0]:6d}, s={x[1][1]:6d}"
                      f" (post: {x[1][2]}, comment: {x[1][3]})\n",
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
    top=5,
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
        if verbose > -1:
            print(f'Retrieving tickers for {sub}', flush=True)
        to_buy = get_tickers(sub, stock_list, prev_tickers, score=score,
                             nPosts=nPosts, top=top, verbose=verbose)
        for stock in to_buy:
            if stock not in positions:
                positions.append(stock)

    print('💵  🚀  DONE!!  🚀  💵')
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
        verbose=args.verbose,
    )
