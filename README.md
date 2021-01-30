# LexUtils
This is a collection of tools that can be run from a REPL to improve Wikidata.

LexUtils can be used as a library if you want. It contains the following modules:
* config: setting up variables that affect all scripts
* riksdagen: code related to the Riksdagen API
* util: code reused among the other modules
* tui.py User Interface specific code

## Requirements
* Python >= 3.7 (datetime fromisoformat needed)
* httpx
* wikibaseintegrator

Install using pip:
`$ sudo pip install wikibaseintegrator httpx`

If pip fails with errors related to python 2.7 you need to upgrade your OS. E.g. if you are using an old version of Ubuntu like 18.04.

## Getting started
To get started install the following libraries with your package manager or
python PIP:
* httpx
* wikibaseintegrator

Please create a bot password for running the script for
safety reasons here: https://www.wikidata.org/wiki/Special:BotPasswords

Add the following variables to your ~/.bashrc (recommended): 
export LEXUTIL_USERNAME="username"
export LEXUTIL_PASSWORD="password"

Alternatively edit the file named config.py yourself and adjust the following
content:

username = "username"
password= "password"

And delete the 2 lines related to environment labels.

