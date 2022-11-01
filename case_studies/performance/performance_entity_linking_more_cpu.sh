#!/bin/bash
PUBMED_SAMPLE="../data/pubmed/pubmed_10k.json"
PHARMACY_VOCAB="../data/pubmed/pubpharm_vocab_2022.tsv"

WIKIPEDIA_DOC="../data/wikipedia/wikipedia_scientists.json"
WIKIDATA_VOCAB="../data/wikipedia/wikidata_vocab.tsv"

POLLUX_DOC="../data/pollux/pollux_docs.json"
POLLUX_VOCAB="../data/pollux/cwe_vocab.tsv"

python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $PUBMED_SAMPLE -c pubmed_benchmark

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $PUBMED_SAMPLE -c pubmed_benchmark -v $PHARMACY_VOCAB --skip-load -f --workers 100 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. Vocab Linking PubMed: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $PUBMED_SAMPLE -c pubmed_benchmark -v $PHARMACY_VOCAB --skip-load -f --workers 100 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. Vocab Linking PubMed: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $PUBMED_SAMPLE -c pubmed_benchmark -v $PHARMACY_VOCAB --skip-load -f --workers 100  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. Vocab Linking PubMed: ${DIFF}s"



python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $WIKIPEDIA_DOC -c scientists_benchmark 2>> /dev/null 1>>/dev/null

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c scientists_benchmark $WIKIPEDIA_DOC --skip-load 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. Stanza NER Wikipedia: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c scientists_benchmark $WIKIPEDIA_DOC --skip-load 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. Stanza NER Wikipedia: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c scientists_benchmark $WIKIPEDIA_DOC --skip-load 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. Stanza NER Wikipedia: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $WIKIPEDIA_DOC -c scientists_benchmark -v $WIKIDATA_VOCAB --skip-load -f --workers 100 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. Vocab Linking Wikipedia: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $WIKIPEDIA_DOC -c scientists_benchmark -v $WIKIDATA_VOCAB --skip-load -f --workers 100 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. Vocab Linking Wikipedia: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $WIKIPEDIA_DOC -c scientists_benchmark -v $WIKIDATA_VOCAB --skip-load -f --workers 100  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. Vocab Linking Wikipedia: ${DIFF}s"


python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $POLLUX_DOC -c pollux_benchmark 2>> /dev/null 1>>/dev/null

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c pollux_benchmark $POLLUX_DOC --skip-load  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. Stanza NER Pollux: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c pollux_benchmark $POLLUX_DOC --skip-load 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. Stanza NER Pollux: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/stanza_ner.py -c pollux_benchmark $POLLUX_DOC --skip-load 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. Stanza NER Pollux: ${DIFF}s"


START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $POLLUX_DOC -c pollux_benchmark -v $POLLUX_VOCAB --skip-load -f --workers 100 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "1. Vocab Linking Pollux: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $POLLUX_DOC -c pollux_benchmark -v $POLLUX_VOCAB --skip-load -f --workers 100 2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "2. Vocab Linking Pollux: ${DIFF}s"

START=$(date +%s.%N)
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py $POLLUX_DOC -c pollux_benchmark -v $POLLUX_VOCAB --skip-load -f --workers 100  2>> /dev/null 1>>/dev/null
END=$(date +%s.%N)
DIFF=$(echo "$END - $START" | bc)
echo "3. Vocab Linking Pollux: ${DIFF}s"


