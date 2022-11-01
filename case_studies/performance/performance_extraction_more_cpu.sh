#!/bin/bash
POLLUX_DOC="../data/pollux/pollux_docs.json"
POLLUX_DOC_ENTITIES="../data/pollux/pollux_docs_with_entities.json"


WIKIPEDIA_DOC="../data/wikipedia/wikipedia_scientists.json"
WIKIPEDIA_DOC_ENTITIES="../data/wikipedia/wikipedia_scientists_entities.json"
WIKIPEDIA_RELATION_VOCAB_SMALL="../data/wikipedia/relation_vocab_small.json"

PUBMED_SAMPLE="../data/pubmed/pubmed_10k_with_entities.json"
WIKIPEDIA_PATHIE_OUTPUT_TEMP="../data/wikipedia/pathie_performance.tsv"
PUBMED_PATHIE_OUTPUT_TEMP="../data/pubmed/pathie_performance.tsv"
PUBMED_RELATION_VOCAB="../data/pubmed/pharm_relation_vocab.json"



START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $WIKIPEDIA_RELATION_VOCAB_SMALL --workers 96 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE Wikipedia: ${DIFF}s - 96"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 96 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE Wikipedia: ${DIFF}s - 96"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 96 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE Wikipedia: ${DIFF}s - 96"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 96 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE PubMed: ${DIFF}s - 96"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 96 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE PubMed: ${DIFF}s - 96"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 96 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE PubMed: ${DIFF}s - 96"






START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $WIKIPEDIA_RELATION_VOCAB_SMALL --workers 48 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE Wikipedia: ${DIFF}s - 48"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 48 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE Wikipedia: ${DIFF}s - 48"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 48 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE Wikipedia: ${DIFF}s - 48"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 48 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE PubMed: ${DIFF}s - 48"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 48 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE PubMed: ${DIFF}s - 48"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 48 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE PubMed: ${DIFF}s - 48"






START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $WIKIPEDIA_RELATION_VOCAB_SMALL --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE Wikipedia: ${DIFF}s - 32"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE Wikipedia: ${DIFF}s - 32"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE Wikipedia: ${DIFF}s - 32"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE PubMed: ${DIFF}s - 32"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE PubMed: ${DIFF}s - 32"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE PubMed: ${DIFF}s - 32"








START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $WIKIPEDIA_RELATION_VOCAB_SMALL --workers 24 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE Wikipedia: ${DIFF}s - 24"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 24 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE Wikipedia: ${DIFF}s - 24"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 24 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE Wikipedia: ${DIFF}s - 24"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 24 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE PubMed: ${DIFF}s - 24"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 24 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE PubMed: ${DIFF}s - 24"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 24 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE PubMed: ${DIFF}s - 24"




START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $WIKIPEDIA_RELATION_VOCAB_SMALL --workers 10 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE Wikipedia: ${DIFF}s - 10"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 10 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE Wikipedia: ${DIFF}s - 10"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 10 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE Wikipedia: ${DIFF}s - 10"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 10 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE PubMed: ${DIFF}s - 10"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 10 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE PubMed: ${DIFF}s - 10"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PUBMED_PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 10 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE PubMed: ${DIFF}s - 10"





