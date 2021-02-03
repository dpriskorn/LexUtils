# LexUtils
This is a collection of tools that can be run from a REPL to improve Wikidata.

The following tools are currently available:
* LexUse (it previously had it's own repository)
* TODO LexCombine
* ...your tool idea here...

When LexUtils start you can choose a tool. 
TODO enable setting of working language

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
export LEXUTILS_USERNAME="username"
export LEXUTILS_PASSWORD="password"

Alternatively edit the file named config.py yourself and adjust the following
content:

username = "username"
password= "password"

## Debugging

You can enable debugging parameters in config.py (by changing False -> True) and adding "--log=loglevel" to the command line where loglevel is one of
* error
* info
* debug
Debug will give you most information, error will give you the least.
