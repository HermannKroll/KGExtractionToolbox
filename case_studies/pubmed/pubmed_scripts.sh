#!/bin/bash
PUBMED_SAMPLE="../data/pubmed/pubmed_10k.json"
PUBMED_SAMPLE_WITH_ENTITIES="../data/pubmed/pubmed_10k.json"
RELATION_VOCAB="../data/pubmed/pharm_relation_vocab.json"
PHARMACY_VOCAB="../data/pubmed/pubpharm_vocab_2022.tsv"

PATHIE_OUTPUT="../data/pubmed/pathie.tsv"
PUBMED_OPENIE6_EXTRACTIONS="../data/pubmed/openie6.tsv"



# Load all documents
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $PUBMED_SAMPLE_WITH_ENTITIES -c PubMed

# Link entities (can be skipped because entities are contained in sample)
# python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $PUBMED_SAMPLE -c PubMed -v $PHARMACY_VOCAB --skip-load -f --workers 32 2>> /dev/null 1>>/dev/null


# Analyze sentences
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/count_sentences.py $PUBMED_SAMPLE_WITH_ENTITIES

# Run Open IE 6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_EXTRACTIONS  --no_entity_filter

# Load OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed -et OPENIE6_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed -et OPENIE6_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed -et OPENIE6_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed -et OPENIE6_SF --entity_filter only_subject_exact

# Analyze the Tuples
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $PUBMED_OPENIE6_EXTRACTIONS


# PathIE with relation vocab
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pipeline.py -c PubMed -et PathIE --relation_vocab $RELATION_VOCAB --workers 32

# Canonicalize predicates
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates.py -c PubMed --word2vec_model ../data/BioWordVec_PubMed_MIMICIII_d200.bin --relation_vocab $RELATION_VOCAB
