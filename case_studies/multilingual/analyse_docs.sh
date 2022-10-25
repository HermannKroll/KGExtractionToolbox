#!/bin/bash
WIKIPEDIA_DOC_ENTITIES="entity_linking/wikipedia_scientists_ml_entities.json"
POLLUX_DOC_ENTITIES="entity_linking/pollux_docs_with_entities.json"
PUBMED_SAMPLE_WITH_ENTITIES="entity_linking/pharmacy_docs_with_entities.json"

python3 compare_translation.py $WIKIPEDIA_DOC_ENTITIES
python3 compare_translation.py $PUBMED_SAMPLE_WITH_ENTITIES
python3 compare_translation.py $POLLUX_DOC_ENTITIES