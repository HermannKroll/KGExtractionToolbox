# Getting Started
This Readme belongs to our JCDL2022 submission. 
```
@inproceedings{kroll2022jcdl,
	title = {A Library Perspective on Nearly-Unsupervised Information Extraction Workflows in Digital Libraries},
	booktitle = {ACM/IEEE Joint Conference on Digital Libraries (JCDL '22)},
	year = {2022},
	month = {06},
	address = {Cologne, Germany},
	doi={10.1145/3529372.3530924},
	author = {Hermann Kroll and Jan Pirklbauer and Florian Plötzky and Wolf-Tilo Balke}
}
```

# Content
We performed case studies in three domains:
- PubMed (10k randomly chosen abstracts that contain a drug)
- Pollux (10k randomly chosen abstracts)
- Wikipedia articles (2.4k full text articles about scientists)


We provide the following data for each case study:
- Document samples
- Used entity vocabularies
- Used relation vocabularies

Note that we selected scientists that must have an Wikipedia page and Wikidata entry.
We zipped the data directory to reduce the GitHub repository size.
So unzip [it](case_studies/data.zip) first.


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
We implemented to improve our toolbox:
- a subject entity filter ([Code](src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py))
- enhanced verb phrase filter options ([Code](src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py))
- improved Open IE6 handling ([Code](src/kgextractiontoolbox/extraction/openie6/main.py))
- Open IE6 analysis ([Code](src/kgextractiontoolbox/extraction/analyze_openie_tuples.py))
- sentence analysis ([Code](src/kgextractiontoolbox/document/count_sentences.py))