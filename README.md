# LexUtils
This is a collection of tools that can be run from a read–eval–print loop (REPL) to improve Wikidata.

When LexUtils start you can choose on of the following tools currently available:
* LexUse (it previously had it's own repository)
* ...your tool idea here... [see So9qs ideas](https://www.wikidata.org/wiki/User:So9q/Tool_ideas) 

## Requirements
* Python >= 3.7 (datetime fromisoformat needed)
* see requirements.txt file for libraries needed

Install using pip:
`$ sudo pip install -r requirements.txt

If pip fails with errors related to python 2.7 you need to upgrade your OS. E.g. if you are using an old version of Ubuntu like 18.04.

## Getting started
Please create a bot password for running the script for
safety reasons here: https://www.wikidata.org/wiki/Special:BotPasswords

Copy or rename the file config.example.py to config.py and adjust the following
variables:

username = "username"
password= "password"

## Debugging

You can enable debugging parameters in config.py (by changing False -> True) and adding "--log=loglevel" to the command line where loglevel is one of:
* error
* info
* debug

Debug will give you most information, error will give you the least.
