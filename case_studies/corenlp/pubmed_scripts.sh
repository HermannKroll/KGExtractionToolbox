#!/bin/bash

PUBMED_SAMPLE_WITH_ENTITIES="../data/pubmed/pubmed_10k_with_entities.json"
PUBMED_CORENLP_OPENIE_EXTRACTIONS="../data/pubmed/corenlp.tsv"


# Load all documents
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $PUBMED_SAMPLE_WITH_ENTITIES -c PubMed

# Run CoreNLP OpenIE
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $PUBMED_SAMPLE_WITH_ENTITIES $PUBMED_CORENLP_OPENIE_EXTRACTIONS --no_entity_filter

# Load CoreNLP OpenIE
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_CORENLP_OPENIE_EXTRACTIONS -c PubMed -et CORENLP_OPENIE_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_CORENLP_OPENIE_EXTRACTIONS -c PubMed -et CORENLP_OPENIE_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_CORENLP_OPENIE_EXTRACTIONS -c PubMed -et CORENLP_OPENIE_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_CORENLP_OPENIE_EXTRACTIONS -c PubMed -et CORENLP_OPENIE_SF --entity_filter only_subject_exact

# Analyze the Tuples
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $PUBMED_CORENLP_OPENIE_EXTRACTIONS

