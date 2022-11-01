#!/bin/bash
# Input
PUBMED_SAMPLE="articles_pharmacy_sentences.json"
RELATION_VOCAB="../data/pubmed/pharm_relation_vocab.json"
PHARMACY_VOCAB="../data/pubmed/pubpharm_vocab_2022.tsv"

# Output
PUBMED_SAMPLE_WITH_ENTITIES="entity_linking/pharmacy_docs_with_entities.json"
PATHIE_OUTPUT="extraction/pathie.tsv"
PUBMED_OPENIE6_EXTRACTIONS="extraction/openie6.tsv"

# Make directories
mkdir entity_linking
mkdir extraction


# Load all documents
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $PUBMED_SAMPLE -c PubMed_ml

# Link entities
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $PUBMED_SAMPLE -c PubMed_ml -v $PHARMACY_VOCAB --skip-load -f --workers 32 2>> /dev/null 1>>/dev/null

# Export Documents
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/export.py $PUBMED_SAMPLE_WITH_ENTITIES -c PubMed_ml -d -t


# Analyze sentences
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/count_sentences.py $PUBMED_SAMPLE_WITH_ENTITIES

# Run Open IE 6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_EXTRACTIONS  --no_entity_filter


# Load OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_ml -et OPENIE6_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_ml -et OPENIE6_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_ml -et OPENIE6_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_ml -et OPENIE6_SF --entity_filter only_subject_exact

# Analyze the Tuples
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $PUBMED_OPENIE6_EXTRACTIONS


# PathIE with relation vocab
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pipeline.py -c PubMed_ml -et PathIE --relation_vocab $RELATION_VOCAB --workers 32

# Canonicalize predicates
#python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates.py -c PubMed_ml --word2vec_model ../data/BioWordVec_PubMed_MIMICIII_d200.bin --relation_vocab $RELATION_VOCAB
