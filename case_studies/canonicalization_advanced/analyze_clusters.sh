#!/bin/bash

# We used the Wikipedia Word Embedding
# Load Word2Vec model
# wget https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates_by_clustering_analysis.py --word2vec_model /home/kroll/workingdir/wiki.en.bin -c scientists_canon
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates_by_clustering_analysis.py --word2vec_model /home/kroll/workingdir/wiki.en.bin -c PubMed_canon
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/cleaning/canonicalize_predicates_by_clustering_analysis.py --word2vec_model /home/kroll/workingdir/wiki.en.bin -c pollux_canon