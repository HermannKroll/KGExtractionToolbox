WIKIPEDIA_CORENLP_EXTRACATIONS="../data/wikipedia/corenlp.tsv"
PUBMED_CORENLP_OPENIE_EXTRACTIONS="../data/pubmed/corenlp.tsv"
POLLUX_CORENLP_EXTRACATIONS="../data/pollux/corenlp.tsv"

# Analyze extractions
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples_complex.py $WIKIPEDIA_CORENLP_EXTRACATIONS
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples_complex.py $PUBMED_CORENLP_OPENIE_EXTRACTIONS
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/analyze_openie_tuples_complex.py $POLLUX_CORENLP_EXTRACATIONS
