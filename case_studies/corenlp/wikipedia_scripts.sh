#!/bin/bash
WIKIPEDIA_DOC_ENTITIES="../data/wikipedia/wikipedia_scientists_entities.json"
WIKIPEDIA_CORENLP_EXTRACATIONS="../data/wikipedia/corenlp.tsv"


python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $WIKIPEDIA_DOC_ENTITIES -c scientists
# Next Delete all short entities
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/delete_short_tags.py 5 -c scientists


# run CORENLP_OPENIE
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_CORENLP_EXTRACATIONS  --no_entity_filter


# Load CORENLP_OPENIE
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_CORENLP_EXTRACATIONS -c scientists -et CORENLP_OPENIE_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_CORENLP_EXTRACATIONS -c scientists -et CORENLP_OPENIE_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_CORENLP_EXTRACATIONS -c scientists -et CORENLP_OPENIE_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $WIKIPEDIA_CORENLP_EXTRACATIONS -c scientists -et CORENLP_OPENIE_SF --entity_filter only_subject_exact


# Analyze extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $WIKIPEDIA_CORENLP_EXTRACATIONS




