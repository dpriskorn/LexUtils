# LexUtils

*NOTE: rewrite in progress. This is in alpha state right now.*

This is a collection of tools that can be run from a read–eval–print loop (REPL) to improve Wikidata.

When LexUtils start you can choose on of the following tools currently available:
* UsageExamples (successor to LexUse)
* Lexeme Statistics
* ...your tool idea here... [see So9qs ideas](https://www.wikidata.org/wiki/User:So9q/Tool_ideas) 

## Requirements
* Python >= 3.7 (datetime fromisoformat needed)
* see requirements.txt file for libraries needed

Install using pip:
`$ sudo pip install -r requirements.txt`

If pip fails with errors related to python 2.7 you need to upgrade your OS. E.g. if you are using an old version of Ubuntu like 18.04.

## Getting started
Please create a bot password for running the script for
safety reasons here: https://www.wikidata.org/wiki/Special:BotPasswords

Copy or rename the file config.example.py to config.py and adjust the following
variables:
```
username = "username"
password = "password"
```
## Use
When you get a prompt like "[Y/n]" the capitalized selection can be selected by
pressing Enter. To select "n" type "n" followed by Enter.

## UsageExamples
Warning: Currently only senses with a gloss in the current working 
language are fetched and shown to the user.

This tool enables you to easily find usage examples 
for any lexeme form (in the supported languages) in 
Wikidata that does not already have one.

Being a CLI tool it enables you to quickly screw things up, 
so please be careful using it.

Currently it does not support editgroups so if you need to 
rollback a change you have to do it manually.

An earlier implementation, LexUse, 
had sorting of usage examples by length before presentation. 
This has not been implemented yet, 
see https://github.com/dpriskorn/LexUtils/issues/18 and 
feel free to send a pull request :)