#!/bin/bash
POLLUX_DOC="../data/pollux/pollux_docs.json"
POLLUX_DOC_ENTITIES="../data/pollux/pollux_docs_with_entities.json"
POLLUX_CORENLP_OPENIE_EXTRACATIONS_TEST="../data/pollux/extractions/corenlp_openie_benchmark.tsv"

WIKIPEDIA_DOC="../data/wikipedia/wikipedia_scientists.json"
WIKIPEDIA_DOC_ENTITIES="../data/wikipedia/wikipedia_scientists_entities.json"
WIKIPEDIA_CORENLP_OPENIE_EXTRACATIONS_TEST="../data/wikipedia/extractions/corenlp_openie_benchmark.tsv"


PUBMED_SAMPLE="../data/pubmed/pubmed_10k_with_entities.json"
PUBMED_CORENLP_OPENIE_TEMP="../data/pubmed/corenlp_openie_performance.tsv"



START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $POLLUX_DOC $POLLUX_CORENLP_OPENIE_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. CoreNLP OpenIE NF POLLUX: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $POLLUX_DOC $POLLUX_CORENLP_OPENIE_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. CoreNLP OpenIE NF POLLUX: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $POLLUX_DOC $POLLUX_CORENLP_OPENIE_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. CoreNLP OpenIE NF POLLUX: ${DIFF}s"



START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $POLLUX_DOC_ENTITIES $POLLUX_CORENLP_OPENIE_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. CoreNLP OpenIE EF POLLUX: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $POLLUX_DOC_ENTITIES $POLLUX_CORENLP_OPENIE_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. CoreNLP OpenIE EF POLLUX: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $POLLUX_DOC_ENTITIES $POLLUX_CORENLP_OPENIE_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. CoreNLP OpenIE EF POLLUX: ${DIFF}s"



START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $WIKIPEDIA_DOC  $WIKIPEDIA_CORENLP_OPENIE_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. CoreNLP OpenIE NF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $WIKIPEDIA_DOC  $WIKIPEDIA_CORENLP_OPENIE_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. CoreNLP OpenIE NF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $WIKIPEDIA_DOC  $WIKIPEDIA_CORENLP_OPENIE_EXTRACATIONS_TEST  --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. CoreNLP OpenIE NF Wikipedia: ${DIFF}s"



START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $WIKIPEDIA_DOC_ENTITIES  $WIKIPEDIA_CORENLP_OPENIE_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. CoreNLP OpenIE EF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $WIKIPEDIA_DOC_ENTITIES  $WIKIPEDIA_CORENLP_OPENIE_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. CoreNLP OpenIE EF Wikipedia: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $WIKIPEDIA_DOC_ENTITIES  $WIKIPEDIA_CORENLP_OPENIE_EXTRACATIONS_TEST  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. CoreNLP OpenIE EF Wikipedia: ${DIFF}s"




START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $PUBMED_SAMPLE $PUBMED_CORENLP_OPENIE_TEMP --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. CoreNLP OpenIE NF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $PUBMED_SAMPLE $PUBMED_CORENLP_OPENIE_TEMP --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. CoreNLP OpenIE NF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $PUBMED_SAMPLE $PUBMED_CORENLP_OPENIE_TEMP --no_entity_filter 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. CoreNLP OpenIE NF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $PUBMED_SAMPLE $PUBMED_CORENLP_OPENIE_TEMP 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. CoreNLP OpenIE EF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $PUBMED_SAMPLE $PUBMED_CORENLP_OPENIE_TEMP 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. CoreNLP OpenIE EF PubMed: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie/main.py $PUBMED_SAMPLE $PUBMED_CORENLP_OPENIE_TEMP 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. CoreNLP OpenIE EF PubMed: ${DIFF}s"
