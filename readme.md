# lol-bot
Used to keep track of Spencer's stats with a bonus of fun Spencer facts

# Requirements
Python 3.8+. Tested on Python 3.11.
`pip install -r requirements.txt`

# Set-up
In conf.yml, replace YOURTOKENHERE with your discord bot token.

Run the program by executing spencerbot.py

# Running llama
`export PATH=$PATH:/usr/local/go/bin`

Terminal 1:
`./ollama serve`

Terminal 2:
`./ollama run wizard-vicuna`