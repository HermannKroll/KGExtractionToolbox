"""
This module contains constants which point to important directories.
"""
import os
from pathlib import Path


def search_config(start: Path, dirname: Path, filename: Path):
    if not start.is_dir():
        return None
    if not (start / dirname).is_dir() or not (start / dirname / filename).is_file():
        return search_config(start / "..", dirname, filename)
    else:
        return (start / dirname / filename).resolve()


GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

DATA_DIR = os.path.join(GIT_ROOT_DIR, "data")
RESOURCE_DIR = os.path.join(GIT_ROOT_DIR, "resources")
CONFIG_DIR = os.path.join(GIT_ROOT_DIR, "config")
TMP_DIR = os.path.join(GIT_ROOT_DIR, "tmp")

if not os.path.isdir(TMP_DIR):
    os.makedirs(TMP_DIR)

# Preprocessing

ENTITY_LINKING_CONFIG = str(search_config(Path(CONFIG_DIR)/'..', Path('config'), Path('entity_linking.json')))

# Backend for Tagging
BACKEND_CONFIG = str(search_config(Path(CONFIG_DIR) / '..', Path('config'), Path('backend.json')))

# Dict Tagger
DICT_TAGGER_BLACKLIST = os.path.join(RESOURCE_DIR, "dict_tagger_blacklist.txt")

# NLP Config
NLP_CONFIG = str(search_config(Path(CONFIG_DIR) / '..', Path('config'), Path('nlp.json')))
