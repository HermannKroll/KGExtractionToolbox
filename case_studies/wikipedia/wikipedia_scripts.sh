#!/bin/bash
WIKIPEDIA_DOC="../data/wikipedia/wikipedia_scientists.json"
WIKIPEDIA_DOC_ENTITIES="../data/wikipedia/wikipedia_scientists_entities.json"
WIKIDATA_VOCAB="../data/wikipedia/wikidata_vocab.tsv"

WIKIPEDIA_OPENIE6_EXTRACATIONS="../data/wikipedia/openie6.tsv"

RELATION_VOCAB_SMALL="../data/wikipedia/relation_vocab_small.json"
RELATION_VOCAB_PERSON="../data/wikipedia/relation_vocab_person.json"



# Load document content
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $WIKIPEDIA_DOC -c scientists


# Analyze sentences
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/count_sentences.py $WIKIPEDIA_DOC_ENTITIES



# First perform Stanza NER
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c scientists $WIKIPEDIA_DOC
# Perform EL with our dictionaries
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $WIKIPEDIA_DOC -c scientists -v $WIKIDATA_VOCAB --skip-load -f

# Next Delete all short entities
# See SQL statements for DB


# run OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC $WIKIPEDIA_OPENIE6_EXTRACATIONS  --no_entity_filter


# Load OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists -et OPENIE6_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists -et OPENIE6_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists -et OPENIE6_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists -et OPENIE6_SF --entity_filter only_subject_exact


# Analyze extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $WIKIPEDIA_OPENIE6_EXTRACATIONS


# PathIE with relation vocab
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pipeline.py -c scientists -et PathIE --relation_vocab $RELATION_VOCAB_SMALL --workers 32

# canonicalize with small vocabulary
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates.py -c scientists --relation_vocab $RELATION_VOCAB_SMALL --min_predicate_threshold 0

# canonicalize with small vocabulary with word embeddings
# python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates.py -c scientists --relation_vocab $RELATION_VOCAB_PERSON --min_predicate_threshold 0 --min_distance 1.0 --word2vec /home/jan/models/wiki.en.bin



