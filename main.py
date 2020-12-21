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


def get_tickers(sub, stock_list, prev_tickers, nPosts=-1):
    reddit = praw.Reddit(
        client_id=config.api_id,
        client_secret=config.api_secret,
        user_agent=config.api_user_agent,
    )
    weekly_tickers = {}

    regex_pattern = r'\b([A-Z]+)\b'
    ticker_dict = stock_list
    blacklist = ["A", "I", "DD", "WSB", "YOLO", "RH", "EV"]
    for (i, submission) in enumerate(reddit.subreddit(sub).top("week")):
        if nPosts > 0:
            print(f'Processing submission {i} of {nPosts}')
            if i == nPosts:
                break
        strings = [submission.title]
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            strings.append(comment.body)
        for s in strings:
            for phrase in re.findall(regex_pattern, s):
                if phrase not in blacklist:
                    if phrase in ticker_dict:
                        if phrase not in weekly_tickers:
                            weekly_tickers[phrase] = 1
                        else:
                            weekly_tickers[phrase] += 1

    top_tickers = sorted(weekly_tickers, key=weekly_tickers.get, reverse=True)[:5]

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
         map(lambda x: x+"\n", to_buy),
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


def main():
    prev_tickers = get_prev_tickers()
    subs = ["wallstreetbets", "stocks", "investing", "smallstreetbets"]
    stock_list = get_stock_list()
    positions = []
    for sub in subs:
        print(f'Retrieving tickers for {sub}')
        to_buy = get_tickers(sub, stock_list, prev_tickers)
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
    main()
