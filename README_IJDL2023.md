# IJDL2022 Submission
This repository belongs to our submission to the International Journal on Digital Libraries. 
The submission extends our previous work published at JCDL. 
The Readme for the JCDL case studies can be found [here](README_CASE_STUDIES.md).

This Readme summarizes the following extensions:
1. Analysis of the noun phrase complexity,
2. CoreNLP OpenIE analysis,
3. Advanced canonicalization via clustering,
4. Extraction from German texts through German-to-English translation.

All relevant data of these studies can be found in this GitHub repository. 
Please check out the [case_studies](case_studies) folder.

### A Note on Reproducibility
To reproduce our results, entity vocabularies are necessary. Therefore, unzip the [data](case_studies/data.zip) first.
The extracted folder must be located inside the [case_studies](case_studies) folder.

Due to the size of the results, we could not upload all OpenIE6 and CoreNLP extraction results into this repository (the samples are contained).
We made this data available at [OneDrive](https://1drv.ms/u/s!ArDgbq3ak3Zuh8x76u4UmrcZ9LrdtQ?e=A5Yzlg).
In this folder are two files: 1. a data_all.zip with all results, and 2. a SQLite database that contained all data that we produced in our case studies.


## 1. Analysis of noun phrase complexity
The first case study was motivated by analyzing the OpenIE noun phrase complexity in more detail. 
In our original paper, we just developed an [own heuristic](src/kgextractiontoolbox/extraction/analyze_openie_tuples.py).
Here, we compared this heuristic to POS-tagged and Sentence-length-based methods.

We developed additional scripts to analyze the noun phrase complexity in more detail.
The scripts can be found [here](case_studies/complexity).
First, the OpenIE 6 extraction must be performed. 
Then its results can be analyzed.
The actual logic to analyze the results can be found [here (Python Code)](src/kgextractiontoolbox/extraction/analyze_openie_tuples_complex.py).

The results can be found here: [CoreNLP OpenIE](case_studies/complexity/results/corenlp_results.txt) and [OpenIE6](case_studies/complexity/results/corenlp_results.txt).

## 2. CoreNLP OpenIE analysis
To generalize the findings of our paper, we analyzed a second OpenIE tool: [CoreNLP OpenIE](https://stanfordnlp.github.io/CoreNLP/openie.html). 
The scripts to reproduce our CoreNLP OpenIE investigation can be found [here](case_studies/corenlp). 
The produced and analyzed samples can also be found there.

## 3. Advanced canonicalization via clustering
Our toolbox contained a script that can canonicalize verb phrases based on a relation vocabulary.
The idea here was to analyze how well methods like [CESI](https://github.com/malllabiisc/cesi) work in practice.
Therefore, we read the code of the CESI repository and developed a clustering-based verb phrase canonicalization in a similar way.

The Python Code for our advanced clustering-based verb phrase canonicalization was integrated into the toolbox.
There are two scripts: [1. do the actual canonicalization](src/kgextractiontoolbox/cleaning/canonicalize_predicates_by_clustering.py) and [2. a clustering analysis script](src/kgextractiontoolbox/cleaning/canonicalize_predicates_by_clustering_analysis.py). 

The scripts and produced data can be found [here](case_studies/canonicalization_advanced).


## 4. Extraction from German texts through German-to-English translation
We decided to investigate how the toolbox can be transferred to another language.
Due to the lack of available NLP tools for other languages, especially OpenIE tools, we decided to translate German texts into English texts.
Then we analyzed the results.

The scripts and data for the multilingual case study can be found [here](case_studies/multilingual).
Note that we manually copied the texts to the DeepL online service to derive the translations.

The data format looks like this:
```
{
 'pollux': {
    'titel':
      'en': "<englisch abstract>",
      'de': "<german abstract>",
      'deepl_en': "<german-to-english translated abstract>",
      'deepl_de': "<english-to-german translated abstract>"
  }
 'wikipedia': {
    'name of scientist':
      'en': "<englisch abstract>",
      'de': "<german abstract>",
      'deepl_en': "<german-to-english translated abstract>",
      'deepl_de': "<english-to-german translated abstract>"
  },
   'pharmacy': {
    'titel':
      'en': "<englisches Abstract>",
      'de': "<deutsches Abstract>",
      'deepl_en': "<übersetztes deutsches Abstract>",
      'deepl_de': "<übersetztes englisches Abstract>"
  }
}
```
The corresponding JSON data sample can be found [here](case_studies/multilingual/de_en_sample_data.json).


