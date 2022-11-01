#!/bin/bash
POLLUX_DOC_ENTITIES="../data/pollux/pollux_docs_with_entities.json"

POLLUX_CORENLP_EXTRACATIONS="../data/pollux/corenlp.tsv"

# Load Pollux documents with tags
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $POLLUX_DOC_ENTITIES -c pollux

# Analyze sentences
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/count_sentences.py $POLLUX_DOC_ENTITIES

# run CoreNLP
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $POLLUX_DOC_ENTITIES $POLLUX_CORENLP_EXTRACATIONS --no_entity_filter

# Load CoreNLP OpenIE Extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_CORENLP_EXTRACATIONS -c pollux -et CORENLP_OPENIE_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_CORENLP_EXTRACATIONS -c pollux -et CORENLP_OPENIE_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_CORENLP_EXTRACATIONS -c pollux -et CORENLP_OPENIE_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $POLLUX_CORENLP_EXTRACATIONS -c pollux -et CORENLP_OPENIE_SF --entity_filter only_subject_exact


# Analyze the extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples.py $POLLUX_CORENLP_EXTRACATIONS
