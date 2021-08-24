import logging

from lexutils.models.wikidata import LexemeStatistics

logging.basicConfig(level=logging.INFO)


def main():
    stats = LexemeStatistics()