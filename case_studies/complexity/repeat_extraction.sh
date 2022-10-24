WIKIPEDIA_DOC="../data/wikipedia/wikipedia_scientists.json"
WIKIPEDIA_OPENIE6_EXTRACATIONS="../data/wikipedia/openie6.tsv"

POLLUX_DOC="../data/pollux/pollux_docs.json"
POLLUX_OPENIE6_EXTRACATIONS="../data/pollux/openie6.tsv"

PUBMED_SAMPLE="../data/pubmed/pubmed_10k.json"
PUBMED_OPENIE6_EXTRACTIONS="../data/pubmed/openie6.tsv"

# Repeat the OpenIE 6 extraction
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC $WIKIPEDIA_OPENIE6_EXTRACATIONS  --no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC $POLLUX_OPENIE6_EXTRACATIONS  --no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_EXTRACTIONS  --no_entity_filter
