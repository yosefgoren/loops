import json

SOURCES = json.load(open("sources.json", 'r'))
PREFIX = SOURCES["prefix"]
SUFFIXES = SOURCES["suffixes"]
