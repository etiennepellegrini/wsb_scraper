import json
import sys
import os

inFile = sys.argv[1]

ticks = json.load(open(inFile, 'r'))

urls=''
for tick in ticks:
    urls+= "https://reddit.com/" + ticks[tick]['topSubmission']['link'] + " "

os.system(f"/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --new-window {urls}")

