#!/bin/bash
POLLUX_DOC="../data/pollux/pollux_docs.json"
POLLUX_DOC_ENTITIES="../data/pollux/pollux_docs_with_entities.json"
POLLUX_VOCAB="../data/pollux/cwe_vocab.tsv"

POLLUX_OPENIE6_EXTRACATIONS="../data/pollux/openie6.tsv"
POLLUX_OPENIE6_RELATION_EXPORT="extraction/openie6_relations.tsv"


# Analyze the vocabulary
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/tagging/vocabulary_analysis.py $POLLUX_VOCAB
# Entity Linking can be skipped (POLLUX_DOC_ENTITIES contains entity annotations)
# Load document content
# python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $POLLUX_DOC -c pollux

# First perform Stanza NER
# python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c pollux $POLLUX_DOC
# Perform EL with our dictionaries
# python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $POLLUX_DOC -c pollux -v $POLLUX_VOCAB --skip-load -f


python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $POLLUX_DOC_ENTITIES -c pollux


# Analyze sentences
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/count_sentences.py $POLLUX_DOC_ENTITIES

# run OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC $POLLUX_OPENIE6_EXTRACATIONS  --no_entity_filter

# Load OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_OPENIE6_EXTRACATIONS -c pollux -et OPENIE6_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_OPENIE6_EXTRACATIONS -c pollux -et OPENIE6_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_OPENIE6_EXTRACATIONS -c pollux -et OPENIE6_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_OPENIE6_EXTRACATIONS -c pollux -et OPENIE6_SF --entity_filter only_subject_exact

python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/export_predicate_mappings.py $POLLUX_OPENIE6_RELATION_EXPORT --collection pollux

# Analyze the extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $POLLUX_OPENIE6_EXTRACATIONS
