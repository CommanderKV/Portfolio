# ---------------------------------------------------------------------------
#     Code obtained from https://github.com/ozh/github-colors/tree/master
#     I do not take any credit for this code, I used it to get the colors 
#                 of all the programming languages on GitHub.
#
#     I have modified the code to return the json instead of writing it.
# ---------------------------------------------------------------------------
import json
import requests
import sys
import yaml
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote
from collections import OrderedDict
from datetime import datetime


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """
    Parse the first YAML document in a stream
    and produce the corresponding Python Orderered Dictionary.
    """
    class OrderedLoader(Loader):
        pass
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: object_pairs_hook(loader.construct_pairs(node)))

    return yaml.load(stream, OrderedLoader)


def order_by_keys(dict):
    """
    Sort a dictionary by keys, case insensitive ie [ Ada, eC, Fortran ]
    Default ordering, or using json.dump with sort_keys=True, produces
    [ Ada, Fortran, eC ]
    """
    from collections import OrderedDict
    return OrderedDict(sorted(dict.items(), key=lambda s: s[0].lower()))


def get_file(url):
    """
    Return the URL body, or False if page not found

    Keyword arguments:
    url -- url to parse
    """
    try:
        r = requests.get(url)
    except:
        sys.exit("Request fatal error :  %s" % sys.exc_info()[1])

    if r.status_code != 200:
        return False

    return r.text

def is_dark(color):
    l = 0.2126 * int(color[0:2], 16) + 0.7152 * int(color[2:4], 16) + 0.0722 * int(color[4:6], 16)
    return False if l / 255 > 0.65 else True

def run():
    # Get list of all langs
    print("Getting list of languages ...")
    yml = get_file("https://raw.githubusercontent.com/github/linguist/master/"
                   "lib/linguist/languages.yml")
    langs_yml = ordered_load(yml)
    langs_yml = order_by_keys(langs_yml)

    # List construction done, count keys
    lang_count = len(langs_yml)
    print("Found %d languages" % lang_count)

    # Construct the wanted list
    langs = OrderedDict()
    for lang in langs_yml.keys():
        if ("type" not in langs_yml[lang] or
                "color" in langs_yml[lang] or
                langs_yml[lang]["type"] == "programming"):
            langs[lang] = OrderedDict()
            langs[lang]["color"] = langs_yml[lang]["color"] if "color" in langs_yml[lang] else None
            langs[lang]["url"] = "https://github.com/trending?l=" + (langs_yml[lang]["search_term"] if "search_term" in langs_yml[lang] else lang)
            langs[lang]["url"] = langs[lang]["url"].replace(' ','-').replace('#','sharp')
    
    print("Processed %d languages" % len(langs))
    return langs
