#!/bin/bash
# Inputs
WIKIPEDIA_DOC="articles_wikipedia_sentences.json"
WIKIDATA_VOCAB="../data/wikipedia/wikidata_vocab.tsv"
RELATION_VOCAB_SMALL="../data/wikipedia/relation_vocab_small.json"
RELATION_VOCAB_PERSON="../data/wikipedia/relation_vocab_person.json"


# Outputs
WIKIPEDIA_DOC_ENTITIES="entity_linking/wikipedia_scientists_ml_entities.json"
WIKIPEDIA_OPENIE6_EXTRACATIONS="extraction/wikipedia_scientists_ml_openie6.tsv"

# Make directories
mkdir entity_linking
mkdir extraction


# Load document content
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $WIKIPEDIA_DOC -c scientists_ml


# First perform Stanza NER
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c scientists_ml $WIKIPEDIA_DOC
# Perform EL with our dictionaries
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $WIKIPEDIA_DOC -c scientists_ml -v $WIKIDATA_VOCAB --skip-load -f

# Next Delete all short entities
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/delete_short_tags.py 5 -c scientists_ml


# Export Documents
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/export.py $WIKIPEDIA_DOC_ENTITIES -c scientists_ml -d -t

# Analyze sentences
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/count_sentences.py $WIKIPEDIA_DOC_ENTITIES


# run OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC $WIKIPEDIA_OPENIE6_EXTRACATIONS  --no_entity_filter


# Load OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists_ml -et OPENIE6_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists_ml -et OPENIE6_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists_ml -et OPENIE6_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_OPENIE6_EXTRACATIONS -c scientists_ml -et OPENIE6_SF --entity_filter only_subject_exact


# Analyze extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $WIKIPEDIA_OPENIE6_EXTRACATIONS


# PathIE with relation vocab
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pipeline.py -c scientists_ml -et PathIE --relation_vocab $RELATION_VOCAB_SMALL --workers 32

# canonicalize with small vocabulary
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates.py -c scientists_ml --relation_vocab $RELATION_VOCAB_SMALL --min_predicate_threshold 0

# canonicalize with small vocabulary with word embeddings
# Load Word2Vec model
# wget https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip
# python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates.py -c scientists_ml --relation_vocab $RELATION_VOCAB_PERSON --min_predicate_threshold 0 --min_distance 1.0 --word2vec /home/jan/models/wiki.en.bin



