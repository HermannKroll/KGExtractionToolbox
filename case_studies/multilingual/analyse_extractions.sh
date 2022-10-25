#!/bin/bash
WIKIPEDIA_OPENIE6_EXTRACATIONS="extraction/wikipedia_scientists_ml_openie6.tsv"
PUBMED_OPENIE6_EXTRACTIONS="extraction/pubmed_openie6.tsv"
POLLUX_OPENIE6_EXTRACATIONS="extraction/pollux_openie6.tsv"

python3 analyze_openie_tuples_with_lang.py $WIKIPEDIA_OPENIE6_EXTRACATIONS
python3 analyze_openie_tuples_with_lang.py $PUBMED_OPENIE6_EXTRACTIONS
python3 analyze_openie_tuples_with_lang.py $POLLUX_OPENIE6_EXTRACATIONS