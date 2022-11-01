#!/bin/bash
PUBMED_SAMPLE="../data/pubmed/pubmed_10k.json"
PUBMED_SAMPLE_WITH_ENTITIES="../data/pubmed/pubmed_10k_with_entities.json"
RELATION_VOCAB="../data/pubmed/pharm_relation_vocab.json"
PUBMED_OPENIE6_EXTRACTIONS="../data/pubmed/openie6.tsv"



# Load all documents with Entities
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/document/load_document.py $PUBMED_SAMPLE_WITH_ENTITIES -c PubMed_canon

# Run Open IE 6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/openie6/main.py $PUBMED_SAMPLE $PUBMED_OPENIE6_EXTRACTIONS  --no_entity_filter


# Load OpenIE6
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_canon -et OPENIE6_NF --entity_filter no_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_canon -et OPENIE6_PF --entity_filter partial_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_canon -et OPENIE6_EF --entity_filter exact_entity_filter
python3 ~/KGExtractionToolbox/src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py $PUBMED_OPENIE6_EXTRACTIONS -c PubMed_canon -et OPENIE6_SF --entity_filter only_subject_exact

