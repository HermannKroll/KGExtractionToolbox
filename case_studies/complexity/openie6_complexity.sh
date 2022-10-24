WIKIPEDIA_OPENIE6_EXTRACATIONS="../data/wikipedia/openie6.tsv"
PUBMED_OPENIE6_EXTRACTIONS="../data/pubmed/openie6.tsv"
POLLUX_OPENIE6_EXTRACATIONS="../data/pollux/openie6.tsv"

# Analyze extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples_complex.py $WIKIPEDIA_OPENIE6_EXTRACATIONS
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples_complex.py $PUBMED_OPENIE6_EXTRACTIONS
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples_complex.py $POLLUX_OPENIE6_EXTRACATIONS
