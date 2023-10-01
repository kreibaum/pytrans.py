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
main_language = config["mainLanguage"]


def all_languages():
    return [main_language['name']] + \
        list(map(lambda x: x['name'], config["translatedTo"]))


# Command Line argument parser
parser = argparse.ArgumentParser(
    description='''Processes json translation files into elm files.
    If you run this without arguments, it rebuilds using the dev language.
    The dev language is stored in a file called .pytrans and configuration
    happens in the pytrans.json file.''')
parser.add_argument('language', metavar='language', type=str, nargs='?',
                    choices=all_languages(),
                    help='Sets the dev language and rebuilds translation files.')
parser.add_argument('--list', action='store_true',
                    help='Shows a list of available languages.')
parser.add_argument('--status', action='store_true',
                    help='Shows active dev language.')
parser.add_argument('--run', nargs=1,
                    help='Runs a script from the config for all languages')
# TODO: A --scaffold would be nice. This would set up a pytrans.json for the
# the user after asking them a few questions.


def write_dot_pytrans(lang):
    with open(".pytrans", "w") as f:
        f.write(lang)


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


def get_language_by_name(name):
    if main_language['name'] == name:
        return main_language
    for lang in config["translatedTo"]:
        if lang['name'] == name:
            return lang


def get_and_write_dev_language(main_language, args):
    '''Checks if the dev language gets changed by command arguments.
    If is changed, this is directly tracked in the config file.'''
    dev_language = main_language
    if args.language is not None:
        dev_language = args.language
        write_dot_pytrans(dev_language)
    else:
        dev_language = read_dot_pytrans(dev_language)
    return get_language_by_name(dev_language)


args = parser.parse_args()

dev_language = get_and_write_dev_language(
    main_language, args)

# Check if we are in --list mode
if args.list:
    print(all_languages())
    sys.exit(0)
# Check if we are in --status mode
elif args.status:
    print(f'Currently selected: {dev_language}')
    sys.exit(0)
# Check if we are in --run mode
elif args.run is not None:
    script_name = args.run[0]
    print(
        f'Running script "{script_name}" from configuration for all languages.')
    script = config["scripts"][script_name]
    for language_name in all_languages():
        print(f'Running "{script_name}" for {language_name}.')
        language = get_language_by_name(language_name)
        for command in script:
            lang_command = command \
                .replace("{name}", language['name']) \
                .replace("{filename}", language['filename']) \
                .replace("{locale}", language['locale'])
            # Run the command in bash
            print(f"> {lang_command}")
            os.system(lang_command)
            pass
    sys.exit(0)

# Make sure input/output exists
input_folder = config["inputFolder"]
output_folder = path.dirname(config["output"])
if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def one_definition(key, value):
    # Custom escape because elm escapes differently from json & from python.
    # It is important, that the "\\" -> "\\\\" happens first, because otherwise
    # it would escape the other escapes.
    value_escaped = value.replace("\\", "\\\\").replace(
        "\"", "\\\"").replace("\n", "\\n")
    return f'{key} : String\n{key} =\n    "{value_escaped}"\n\n\n'


def write_language_file(language_name, data):
    f = open(config["output"], "w")

    f.write("module Translations exposing (..)\n\n")
    f.write(f"{{-| Generated translation file for {language_name}\n-}}\n\n\n")

    f.write(
        f"{{-| List of all supported languages. Default language is {main_language}.\n-}}\n")
    f.write("type Language\n")
    f.write(f"    = {main_language['name']}\n")
    for lang in config["translatedTo"]:
        f.write(f"    | {lang['name']}\n")
    f.write("\n\n")

    f.write(f"{{-| The language that is currently active.\n-}}\n")
    f.write("compiledLanguage : Language\n")
    f.write("compiledLanguage =\n")
    f.write(f"    {language_name['name']}\n\n\n")

    for key in data:
        f.write(one_definition(key, data[key]))


def load_data(language_name):
    return json.load(open(path.join(input_folder, language_name)))


def default_missing_values(translated, defaults):
    result = dict()
    for key in defaults:
        if key in translated:
            result[key] = translated[key]
        else:
            result[key] = defaults[key]
    return result


main_language_data = load_data(main_language['filename'])
data = default_missing_values(
    load_data(dev_language['filename']), main_language_data)
write_language_file(dev_language, data)
