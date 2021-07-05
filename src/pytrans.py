#!/usr/bin/env python3
# Translation tool that reads some JSON files and generates elm files from them.
# I am using this for static translations in pacoplay.com

import json
import os.path as path
import os
import argparse
import sys

# Assumes there is a file named "Config.json" in the current directory and open
# it. Here we can define the main language of the project.
config = json.load(open("pytrans.json"))
main_language_name = config["mainLanguage"]


def all_languages():
    return [main_language_name] + config["translatedTo"]


# Command Line argument parser
parser = argparse.ArgumentParser(
    description='''Processes json translation files into elm files.
    If you run this without arguments, it rebuilds using the dev language.
    The dev language is stored in a file called .pytrans and configurantion
    happens in the pytrans.json file.''')
parser.add_argument('language', metavar='language', type=str, nargs='?',
                    choices=all_languages(),
                    help='Sets the dev language and rebuilds translation files.')
parser.add_argument('--list', action='store_true',
                    help='Shows a list of available languages.')
parser.add_argument('--status', action='store_true',
                    help='Shows active dev language.')
# TODO: A --scaffold would be nice. This would set up a pytrans.json for the
# the user after asking them a few questions.

args = parser.parse_args()


def write_dot_pytrans(lang):
    with open(".pytrans", "w") as f:
        f.write(dev_language)


def read_dot_pytrans(fallback_lang):
    try:
        with open(".pytrans") as f:
            result = f.read()
            if result in all_languages():
                return result
            else:
                raise ValueError(
                    f'Language {result} not supported. Use --list to get all languages.')
    except FileNotFoundError:
        # This is fine, it just means there is no configured dev language. We fall
        # back to the main language in this case.
        return fallback_lang


# Determine development language
dev_language = main_language_name
if args.language is not None:
    dev_language = args.language
    write_dot_pytrans(dev_language)
else:
    dev_language = read_dot_pytrans(dev_language)

# Read currently configured dev language from .pytrans file
if args.list:
    print(all_languages)
    sys.exit(0)
elif args.status:
    print(f'Currently selected: {dev_language}')
    sys.exit(0)


# Make sure input/output exists
input_folder = config["inputFolder"]
if not os.path.exists(config["outputFolder"]):
    os.makedirs(config["outputFolder"])


def one_definition(key, value):
    # Custom escape because elm escapes differently from json & from python.
    value_escaped = value.replace("\"", "\\\"").replace(
        "\\", "\\\\").replace("\n", "\\n")
    return f'{key} : String\n{key} =\n    "{value_escaped}"\n\n\n'


def write_language_file(language_name, data):
    f = open(
        path.join(config["outputFolder"], language_name + ".elm"), "w")

    f.write("module Translations exposing (..)\n\n")
    f.write(f"{{-| Generated translation file for {language_name}\n-}}\n\n\n")

    f.write(
        f"{{-| List of all supported languages. Default language is {main_language_name}.\n-}}\n")
    f.write("type Language\n")
    f.write(f"    = {main_language_name}\n")
    for lang in config["translatedTo"]:
        f.write(f"    | {lang}\n")
    f.write("\n\n")

    f.write(f"{{-| The language that is currently active.\n-}}\n")
    f.write("compiledLanguage : Language\n")
    f.write("compiledLanguage =\n")
    f.write(f"    {language_name}\n\n\n")

    for key in data:
        f.write(one_definition(key, data[key]))


def load_data(language_name):
    return json.load(open(path.join(input_folder, language_name + ".json")))


main_language_data = load_data(main_language_name)
write_language_file(main_language_name, main_language_data)


def default_missing_values(translated, defaults):
    result = dict()
    for key in defaults:
        if key in translated:
            result[key] = translated[key]
        else:
            result[key] = defaults[key]
    return result


for lang in config["translatedTo"]:
    data = default_missing_values(load_data(lang), main_language_data)
    write_language_file(lang, data)
