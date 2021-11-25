# Entity Linking
## Configuration
First, create a copy of the entity linking configuration.
```
cp config/entity_linking.prod.json config/entity_linking.json
```

## Dictionary-based Entity Linker

The dictionary-based entity linker requires an entity vocabulary as its input.
An entity vocabulary may look like:

|id |type |heading      |synonyms            |
|---|--------|-------------|--------------------|
|Q1 |Person  |Barack Obama |Obama;Barack        |
|Q2 |Person  |Angela Merkel|Merkel              |
|Q3 |Location|Honolulu     |                    |
|Q4 |Location|Hamburg      |Hansestadt          |
|Q5 |Location|America      |US;USA;United States|

Each entry has a unique entity id, an entity id, a heading and a list of synonyms. 
We encode an entity vocabulary as a TSV-file:
- each line represents an entity
- ids must be unique
- types can be arbitrary strings
- heading is a string
- synonyms is a list of strings seperated by a ;

An example TSV [entity vocabulary file](resources/entity_linking/el_vocabulary.tsv) looks like:
```
id	type	heading	synonyms
Q1	Person	Barack Obama	Obama;Barack
Q2	Person	Angela Merkel	Merkel
Q3	Location	Honolulu
Q4	Location	Hamburg	Hansestadt
Q5	Location	America	US;USA;United States
```


Next, we use the entity vocabulary to produce annotations. 
The entity linker requires:
- document/documents as its input
- the corresponding document collection
- the vocabulary file

The entity linker will automatically insert documents that are not in the database yet.
```
python src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py DOCUMENT -c COLLECTION -v VOCAB_FILE
```

You can also parallelize the entity linking by adding the *--workers* argument and specify a number of workers.
```
python src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py DOCUMENT -c COLLECTION -v VOCAB_FILE --workers 10
```

By default, the entity linker writes its logs in a temporary directory and deletes this directory by completion.
You can specify a logging directory that will not be deleted:
You can also parallelize the entity linking by adding the *--workers* argument and specify a number of workers.
```
python src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py DOCUMENT -c COLLECTION -v VOCAB_FILE --workdir test/
```


Note that our toolbox won't annotate the same document twice. 
This will be checked automatically.
If your document content has changed, please delete the old table contents (document and doc_tagged_by and tags before).

If your entity vocabulary has changed, you can use the **--force** argument to enforce linking all documents again.
```
python src/kgextractiontoolbox/entitylinking/vocab_entity_linking.py DOCUMENT -c COLLECTION -v VOCAB_FILE --force
```


## Configuration
There are several options that can be specified in a configuration file. 
```
nano config/entity_linking.json
```

You can adjust the setting for the dictionary-based entity linker:
```
#...
  "dict": {
    "max_words": 5, # specifies the maximal number of words an entity has 
    "check_abbreviation": "true", # check custom introduced abbreviations in brackets 
    "custom_abbreviations": "true", # check custom introduced abbreviations in brackets
    "min_full_tag_len": 5 # may improve the quality when working with homonys. An entity is only tagged in a document when a full mention (here 5) characters was detected at least once.
  }
#...
```
# Stanza Named Entity Recognition
Before working with Stanza, you need to setup the English model. 
Therefore, run:
```
python src/kgextractiontoolbox/setup_stanza.py
```
This may take a while.

Next, Stanza can be used to detect Named Entities in documents. 
Note that Stanza does not produce entity ids. Thus, we will use the entity mention string as the entity id.
```
python src/kgextractiontoolbox/entitylinking/stanza_ner.py DOCUMENT -c COLLECTION
```

Stanza will by default run on your GPU. If no GPU is available, you can specificy the CPU flag which will cause a long runtime.
```
python src/kgextractiontoolbox/entitylinking/stanza_ner.py DOCUMENT -c COLLECTION --CPU
```
Note that our toolbox won't annotate the same document twice. 
This will be checked automatically.
If your document content has changed, please delete the old table contents (document and doc_tagged_by and tags before).

## Stanza Config
There are several options that can be specified in a configuration file. 
```
nano config/entity_linking.json
```
By default, Stanza produces many entity annotations that might not be helpful. 
By default, we ignore Ordinals (Number Sequences), Quantities and Percent types. 
You can adjust the entity filter in the configuration.
```
#...
  "stanza": {
    "document_batches": 1000, # how many documents will be processed in one batch (more requires more VRAM)
    "entity_type_blocked_list": ["ORDINAL", "QUANTITY", "PERCENT"] # ignored entity types
  }
#...
```

# Biomedical Entity Linking
Instead of integrating the domain-specific entity linker directly, you may also use them next to our toolbox and only load their outputs.
Additionally, our Pipeline supports two commonly used tools for entity linking in the biomedical domain. 
Namely, these are 
- TaggerOne for Chemicals and Diseases
- GNormPlus for Genes and Species.


## Setup
First, create a directory for the taggers:
```
mkdir ~/tools
```
Download [GNormPlus](https://www.ncbi.nlm.nih.gov/research/bionlp/Tools/gnormplus/) and [TaggerOne](https://www.ncbi.nlm.nih.gov/research/bionlp/tools/taggerone/). Unzip both and move the directories into tools. 
```
tools/
  GNormPlusJava/
  TaggerOne-0.2.1/
```
Both tools require a Java installation. To use TaggerOne, see its readme file. Some models must be build manually.

### Tagger Configuration
Adjust the root path configurations for both taggers in `entity_linking.json:`
```
{
  "taggerOne": {
    "root": "<path to tools>/tools/TaggerOne-0.2.1",  # Taggerone root path here
    "model": "models/model_BC5CDRJ_011.bin",
    "batchSize": 10000,
    "timeout": 15,
    "max_retries": 1
  },
  "gnormPlus": {
    "root": "<path to tools>/tools/GNormPlusJava", # GNormPlus path here
    "javaArgs": "-Xmx16G -Xms10G"
  },
  #...
}
```

If TaggerOne gets stuck on a file, the process will be killed after `"timeout"` minutes without progress. The pipeline will then restart TaggerOne and will retry to process the file `"max_retries"` times. If no progress is made by then, the file will be ignored. 

## Runing the biomedical entity linking
Below you can see a sample call for the pipeline. Run TaggerOne:
```
python src/kgextractiontoolbox/entitylinking/biomedical_entity_linking.py test.json --collection test --tagger-one
```

Run GNormPlus:
```
python src/kgextractiontoolbox/entitylinking/biomedical_entity_linking.py test.json --collection test --gnormplus
```


The pipeline will read the input file `test.json` and will load the contained documents into the database in collection `test`. It will then invoke both taggerOne and GNormPlus, which generate tags as output. The tags will also be inserted into the database. 

You must either select **--tagger-one** or **--gnormplus**. Both linkers must run separately.

For more information and additional options, please see
```
python src/kgextractiontoolbox/entitylinking/biomedical_entity_linking.py --help
```

# Export Annotations
For generating an output file containing the generated tags, please see [04 Export Statements](README_04_EXPORT.md).