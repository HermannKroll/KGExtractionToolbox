#!/bin/bash
POLLUX_DOC="../data/pollux/pollux_docs.json"
POLLUX_DOC_ENTITIES="../data/pollux/pollux_docs_with_entities.json"
POLLUX_OPENIE6_EXTRACATIONS_TEST="../data/pollux/extractions/openie6_benchmark.tsv"


WIKIPEDIA_DOC="../data/wikipedia/wikipedia_scientists.json"
WIKIPEDIA_DOC_ENTITIES="../data/wikipedia/wikipedia_scientists_entities.json"
WIKIPEDIA_OPENIE6_EXTRACATIONS_TEST="../data/wikipedia/extractions/openie6_benchmark.tsv"


PUBMED_SAMPLE="../data/pubmed/pubmed_10k_with_entities.json"
PUBMED_OPENIE6_TEMP="../data/pubmed/openie6_performance.tsv"
PATHIE_OUTPUT_TEMP="../data/pubmed/pathie_performance.tsv"
PUBMED_RELATION_VOCAB="../data/pubmed/pharm_relation_vocab.json"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC $POLLUX_OPENIE6_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. OpenIE6 NF POLLUX: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC $POLLUX_OPENIE6_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. OpenIE6 NF POLLUX: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC $POLLUX_OPENIE6_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. OpenIE6 NF POLLUX: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC_ENTITIES $POLLUX_OPENIE6_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. OpenIE6 EF POLLUX: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC_ENTITIES $POLLUX_OPENIE6_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. OpenIE6 EF POLLUX: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $POLLUX_DOC_ENTITIES $POLLUX_OPENIE6_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. OpenIE6 EF POLLUX: ${DIFF}s"





START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC $WIKIPEDIA_OPENIE6_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. OpenIE6 NF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC $WIKIPEDIA_OPENIE6_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. OpenIE6 NF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC $WIKIPEDIA_OPENIE6_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. OpenIE6 NF Wikipedia: ${DIFF}s"



START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_OPENIE6_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. OpenIE6 EF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_OPENIE6_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. OpenIE6 EF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $WIKIPEDIA_DOC_ENTITIES $WIKIPEDIA_OPENIE6_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. OpenIE6 EF Wikipedia: ${DIFF}s"





START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. PathIE PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. PathIE PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/pathie/main.py $PUBMED_SAMPLE $PATHIE_OUTPUT_TEMP --relation_vocab $PUBMED_RELATION_VOCAB --workers 32 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. PathIE PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_TEMP  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. OpenIE6 NF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_TEMP  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. OpenIE6 NF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_TEMP  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. OpenIE6 NF PubMed: ${DIFF}s"



START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_TEMP  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. OpenIE6 EF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_TEMP  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. OpenIE6 EF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_TEMP  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. OpenIE6 EF PubMed: ${DIFF}s"
