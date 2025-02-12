# ---------------------------------------------------------------------------
#     Code obtained from https://github.com/ozh/github-colors/tree/master
#     I do not take any credit for this code, I used it to get the colors 
#                 of all the programming languages on GitHub.
#
#     I have modified the code to return the json instead of writing it.
#             I have also added logging to the code with logfire.
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
import logfire

@logfire.instrument("Creating yaml stream of colors", extract_args=False)
def ordered_load(stream: str|bool, Loader: yaml.Loader=yaml.Loader, object_pairs_hook: OrderedDict=OrderedDict) -> any:
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


def order_by_keys(dict: dict) -> OrderedDict:
    """
    Sort a dictionary by keys, case insensitive ie [ Ada, eC, Fortran ]
    Default ordering, or using json.dump with sort_keys=True, produces
    [ Ada, Fortran, eC ]
    """
    logfire.info("Sorting dictionary by keys")
    return OrderedDict(sorted(dict.items(), key=lambda s: s[0].lower()))

@logfire.instrument("Getting file from URL")
def get_file(url: str) -> str | bool:
    """
    Return the URL body, or False if page not found

    Keyword arguments:
    url -- url to parse
    """
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as error:
        logfire.fatal(f"Request fatal error: {error}")
        sys.exit(1)

    if r.status_code != 200:
        logfire.error(f"Request error page not found. Response code: {r.status_code}")
        return False

    logfire.info("Request successful")
    return r.text

def is_dark(color: str) -> bool:
    l = 0.2126 * int(color[0:2], 16) + 0.7152 * int(color[2:4], 16) + 0.0722 * int(color[4:6], 16)
    return False if l / 255 > 0.65 else True

@logfire.instrument("Getting colors of all programming languages on GitHub")
def run():
    # Get list of all langs
    logfire.info("Getting colors")
    yml = get_file("https://raw.githubusercontent.com/github/linguist/master/"
                   "lib/linguist/languages.yml")
    langs_yml = ordered_load(yml)
    langs_yml = order_by_keys(langs_yml)

    # List construction done, count keys
    lang_count = len(langs_yml)
    logfire.info("Found %d languages" % lang_count)

    # Construct the wanted list
    langs = OrderedDict()
    logfire.info("Creating dictionary of colors")
    for lang in langs_yml.keys():
        if ("type" not in langs_yml[lang] or
                "color" in langs_yml[lang] or
                langs_yml[lang]["type"] == "programming"):
            langs[lang] = OrderedDict()
            langs[lang]["color"] = langs_yml[lang]["color"] if "color" in langs_yml[lang] else None
            langs[lang]["url"] = "https://github.com/trending?l=" + (langs_yml[lang]["search_term"] if "search_term" in langs_yml[lang] else lang)
            langs[lang]["url"] = langs[lang]["url"].replace(' ','-').replace('#','sharp')
    
    logfire.info(f"Processed {len(langs)} languages")
    return langs
