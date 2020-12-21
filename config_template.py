# Login module template
# Shows how to write `config.py`

#---------------------------------------------------------------------------
# Config.py
#---------------------------------------------------------------------------
# DO NOT DISTRIBUTE!
#---------------------------------------------------------------------------
# Contains login info for RH and Reddit. This should be encrypted or something
# (especially if I put the RH stuff in it) but too lazy for now

# --- Reddit
# PRAW doc: https://praw.readthedocs.io/en/latest/getting_started/quick_start.html

# Step 1: Create Reddit App to get secret
# https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps
api_id="p-jcoLKBynTLew"
api_secret="gko_LXELoV07ZBNUXrvWZfzE3aI"

# From PRAW doc: to use Reddit’s API, you need a unique and descriptive user
# agent. The recommended format is <platform>:<app ID>:<version string> (by
# u/<Reddit username>)
api_user_agent="android:com.example.myredditapp:v1.2.3 (by /u/kemitche)"

#---------------------------------------------------------------------------
