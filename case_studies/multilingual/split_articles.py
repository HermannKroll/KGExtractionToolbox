#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

id: X1 X2 X3
X1(2 Ziffern): Artikel-Identifier
X2: 1 = Wikipedia, 2 = Pollux
X3: 1 = Englisches Abstract, 2 = Deepl-Variante; beides als Python Liste

"""
import json
from collections import defaultdict

from spacy.lang.en import English

DATA_PATH = 'de_en_sample_data.json'

PHARM_PATH = 'articles_pharmacy.json'
POLLUX_PATH = 'articles_pollux.json'
WIKIPEDIA_PATH = 'articles_wikipedia.json'

PHARM_SENT_PATH = 'articles_pharmacy_sentences.json'
POLLUX_SENT_PATH = 'articles_pollux_sentences.json'
WIKIPEDIA_SENT_PATH = 'articles_wikipedia_sentences.json'

WIKI_ID = "1"
POLLUX_ID = "2"
PHARM_ID = "3"
EN_ABSTRACT = "1"
DEEPL_ABSTRACT = "2"


def source2id(source):
    if source == "wikipedia":
        return WIKI_ID
    if source == "pollux":
        return POLLUX_ID
    return PHARM_ID


def abstype2id(abstract_type):
    return EN_ABSTRACT if abstract_type == 'en' else DEEPL_ABSTRACT


def pad_to_three_digits(digit):
    if digit > 99:
        conv = str(digit)
    elif digit > 9:
        conv = "0" + str(digit)
    else:
        conv = "00" + str(digit)
    return conv


def load_file(path: str = DATA_PATH) -> list:
    data = json.load(open(path))
    entries = []
    # flatten the dict
    for k, v in data.items():
        for k1, v1 in data[k].items():
            v2 = v1
            v2['source'] = k
            entries.append(v2)
    return entries


def save_file(data: list, path: str):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':
    result = defaultdict(list)
    result_split_sentences = defaultdict(list)

    spacy_nlp = English()  # just the language with no model
    spacy_nlp.add_pipe("sentencizer")

    for idx, entry in enumerate(load_file()):
        result[entry["source"]].append({
            "id": int(f'{source2id(entry["source"])}{pad_to_three_digits(idx)}{abstype2id("en")}'),
            "title": "",
            "abstract": entry["en"]
        })
        result[entry["source"]].append({
            "id": int(f'{source2id(entry["source"])}{pad_to_three_digits(idx)}{abstype2id("deepl_en")}'),
            "title": "",
            "abstract": entry["deepl_en"]
        })

        for abskey in ('en', 'deepl_en'):

            doc_nlp = spacy_nlp(entry[abskey])

            for sentidx, sentence in enumerate(doc_nlp.sents):
                id = int(
                    source2id(entry['source']) + \
                    pad_to_three_digits(idx + 1) + pad_to_three_digits(sentidx) + abstype2id(abskey)
                )

                result_split_sentences[entry['source']].append({
                    "id": id,
                    "title": "",
                    "abstract": str(sentence)
                })

    # sort by document id
    for k, v in result.items():
        v.sort(key=lambda x: x["id"])

    # sort by sentence id
    for k, v in result_split_sentences.items():
        v.sort(key=lambda x: x["id"])

    save_file(result["pollux"], POLLUX_PATH)
    save_file(result["wikipedia"], WIKIPEDIA_PATH)
    save_file(result["pharmacy"], PHARM_PATH)

    save_file(result_split_sentences["pollux"], POLLUX_SENT_PATH)
    save_file(result_split_sentences["wikipedia"], WIKIPEDIA_SENT_PATH)
    save_file(result_split_sentences["pharmacy"], PHARM_SENT_PATH)
