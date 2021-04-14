#!/usr/bin/env python3
import gettext
from modules import europarl
from typing import Dict

_ = gettext.gettext

# Functions in here only have side-effects

def downloading_from(api_name):
    print(_("Downloading from {}...".format(api_name)))


def europarl_download():
    print(_("Downloading {} sentence file for {}".format(
            europarl.api_name, config.language,
    )))


def working_on(category: str, word: str):
    print(_("Working on the {} {}".format(category, word)))


def number_of_found_sentences(dict_length):
    print(_("Found {} suitable sentences".format(
        dict_length,
    )))


def found_sentence(word_count: int, data: Dict, sentence: str):
    # FIXME add grammatical features here
    print(_("Found the following sentence with {} ".format(word_count) +
            "words. Is it suitable as a usage example " +
            "for the {} form '{}'? \n".format(data['category'], data['word']) +
            "'{}'".format(sentence)))


def fetching_senses():
    print(_("Fetching senses..."))


def cancel_sentence(word: str):
    print(_("Cancelled adding sentence as it does not match the " +
            "only sense currently present. \nLexemes are " +
            "entirely dependent on good quality QIDs. \n" +
            "Please add labels " +
            "and descriptions to relevant QIDs and then use " +
            "MachtSinn to add " +
            "more senses to lexemes by matching on QID concepts " +
            "with similar labels and descriptions in the lexeme " +
            "language." +
            "\nSearch for {} in Wikidata: ".format(word)) +
          "https://www.wikidata.org/w/index.php?" +
          "search={}&title=Special%3ASearch&".format(word) +
          "profile=advanced&fulltext=0&" +
          "advancedSearch-current=%7B%7D&ns0=1")
