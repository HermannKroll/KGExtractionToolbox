# Disclaimer
This repository belongs to our JCDL2022 submission. 
```
A Library Perspective on Nearly-Unsupervised Information Extraction Workflows in Digital Libraries
```
Due to the double-blind review process, we can't publish our case studies as a pull request to GitHub. 
If the paper is accepted, we will make all data publicly available at GitHub.

# Content
We performed case studies in three domains:
- PubMed (10k randomly chosen abstracts that contain a drug)
- Pollux (10k randomly chosen abstracts)
- Wikipedia articles (2.4k full text articles about scientists)


We provide the following data for each case study:
- Document samples
- Used entity vocabularies
- Used relation vocabularies

Note that each scientist must have an Wikipedia page and Wikidata entry.

This repository contains:
- Bash scripts to reproduce our findings
- Bash scripts to measure the performance
- SQL scripts for data analysis

Shortcuts for scripts:
- Pharmacy ([Scripts](case_studies/pubmed/pubmed_scripts.sh), [SQL Queries](case_studies/pubmed/pubmed_queries.sql))
- Political Sciences ([Scripts](case_studies/pollux/pollux_scripts.sh), [SQL Queries](case_studies/pollux/pollux_queries.sql))
- Wikipedia ([Scripts](case_studies/wikipedia/wikipedia_scripts.sh), [SQL Queries](case_studies/wikipedia/wikipedia_queries.sql))
- Performance Measurement ([Entity Linking](case_studies/performance/performance_entity_linking.sh), [Extraction](case_studies/performance/performance_extraction.sh))

Summarized evaluation data can be found in [Summary Directory](case_studies/summary). 

# Repository Organization
To setup the toolbox, please read the original [Readme](README.md). 

The repository is organized as follows:
```
case_studies
       ../data      -- contains the data for each collection
       ../pubmed    -- evaluation scripts + data for pharmacy
       ../pollux    -- evaluation scripts + data for political sciences
       ../wikipedia -- evaluation scripts + data for wikipedia
```

We include randomly selected data that we used for our evaluation.
- Entity linking + Stanza NER
- Open IE 6 + PathIE
- Relation mappings (Canonicalization Evaluation)

The evaluation data is stored in Microsoft Excel XLSX files. 
We also include the original .csv files exported from our case studies.
You can find the data in the corresponding subfolders.
The file names should be self-explaining.

# Code Changes:
We implemented:
- a subject entity filter ([Code](src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py))
- enhanced verb phrase filter options ([Code](src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py))
- improved Open IE6 handling ([Code](src/kgextractiontoolbox/extraction/openie6/main.py))
- Open IE6 analysis ([Code](src/kgextractiontoolbox/extraction/analyze_openie_tuples.py))
- sentence analysis ([Code](src/kgextractiontoolbox/document/count_sentences.py))