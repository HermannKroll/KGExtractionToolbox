"""
This module contains constants which point to important directories.
"""
import os

GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

DATA_DIR = os.path.join(GIT_ROOT_DIR, "data")
RESOURCE_DIR = os.path.join(GIT_ROOT_DIR, "resources")
CONFIG_DIR = os.path.join(GIT_ROOT_DIR, "config")
TMP_DIR = os.path.join(GIT_ROOT_DIR, "tmp")

if not os.path.isdir(TMP_DIR):
    os.makedirs(TMP_DIR)

# Preprocessing
ENTITY_LINKING_CONFIG = os.path.join(CONFIG_DIR, 'entity_linking.json')

# Backend for Tagging
BACKEND_CONFIG = os.path.join(CONFIG_DIR, "backend.json")

# Dict Tagger
DICT_TAGGER_BLACKLIST = os.path.join(RESOURCE_DIR, "dict_tagger_blacklist.txt")

# NLP Config
NLP_CONFIG = os.path.join(CONFIG_DIR, 'nlp.json')
