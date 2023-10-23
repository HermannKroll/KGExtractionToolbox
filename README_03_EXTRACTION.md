

# Setup
The toolbox utilizes three external tools to extract statements from natural language texts. 
We do not require the installation of all tools. 
Please carefully read our paper and the instructions below to select the tools for your purposes.

PathIE requires:
- [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/)
- Stanford Stanza (has to be installed via pip. See Stanza section.)

OpenIE extraction can be produced by one of the following tools:
- [Stanford CoreNLP](https://stanfordnlp.github.io/CoreNLP/)
- [OpenIE 5.1 Standalone](https://github.com/dair-iitd/OpenIE-standalone)
- [OpenIE 6](https://github.com/dair-iitd/openie6)

Note, we did not evaluate OpenIE 5.1 yet, but it seems to be a good compromise between runtime and quality.

Please install the required tools for your purposes. Then, edit the nlp.conf in this directory.
```
cd KGExtractionToolbox/
cp config/nlp.prod.conf config/nlp.conf 
nano config/nlp.conf
```
Then edit the following paths:
```
{
  "corenlp": ".../stanford-corenlp-4.1.0/", # required for PathIE and CoreNLP OpenIE
  "openie6": ".../openie6/", # Optional for OpenIE6
  "openie5.1": { # Optional for OpenIE 5.1
    "port": 8085,
    "jar": ".../OpenIE-standalone/openie-assembly-5.0-SNAPSHOT.jar"
  }
}
```
Note, you only need to edit the paths of tools which you would like to use.

The run bash scripts need to right permissions. Set them by running:
```
bash setup_permissions.sh
```
Finally, we must download nltk data for our extraction methods:
```
python src/kgextractiontoolbox/setup_nltk.py
```


### OpenIE 5.1
OpenIE 5.1 requires some extra setup. Please read [OpenIE 5.1](https://github.com/dair-iitd/OpenIE-standalone).
We have tested the standalone jar. Download it and test if the setup works.

### OpenIE 6
OpenIE 6 requires some extra setup. Please carefully read the [OpenIE 6 setup instructions](https://github.com/dair-iitd/openie6).
You need to create a virtual python environment.
Next, you must edit the run script:
```
src/kgextractiontoolbox/extraction/openie6/run.sh
```

Setup the name to your conda environment (openie6 default):
```
#!/bin/bash
cd $1
conda activate openie6
python run.py --mode splitpredict --inp $2 --out $3 --rescoring --task oie --gpus 1 --oie_model models/oie_model/epoch=14_eval_acc=0.551_v0.ckpt --conj_model models/conj_model/epoch=28_eval_acc=0.854.ckpt --rescore_model models/rescore_model --num_extractions 5
```
Please be sure that your conda activate is configured correctly.

Next, we need an additional Spacy model to lemmatize the OpenIE 6 outputs. 
Install it in the project Python environment by:
```
pip install -U spacy[lookups]
```

# Running the Extraction:
We support two options to run the extraction methods:
- a pipeline method which will automatically export document contents, process them and load the extractions into the database. The pipeline will automatically skip documents that have already been processed by it. This information is stored in the document_processed_by_ie table.
- run the extraction scripts for a method by your own. You will then have the raw extraction outputs available. You have to load them into the database. 


## Extraction Pipeline
The extraction pipeline can process all documents in a document collection at once. 
The process will work in batches to accelerate the extraction.
```
python src/kgextractiontoolbox/extaction/pipeline.py --extraction_type METHOD --collection COLLECTION
```
We support the following methods:
- PathIE
- PathIEStanza
- OpenIE
- OpenIE51
- OpenIE6

If you use an OpenIE method, then you must specify the corresponding entity filtering:
- no_entity_filter (do not filter OpenIE methods)
- partial_entity_filter (Default; force that in subject and object an entity must partially be included)
- exact_entity_filter (force that subject and object must match an entity)
- only_subject_exact (force that subject must match an entity)

```
python src/kgextractiontoolbox/extaction/pipeline.py --extraction_type METHOD --collection COLLECTION --entity_filter no_entity_filter
```


The **--workers** argument allows you to run the execution in parallel. 
Note that PathIEStanza, OpenIE51 and OpenIE6 cannot run in parallel.

If you want to process a list of document ids, you can define this list as a .txt file:
```
100
101
102
```
Then, use the *--idfile* argument to load it.
```
python src/kgextractiontoolbox/extaction/pipeline.py --idfile ids.txt --extraction_type METHOD --collection COLLECTION
```
The pipeline will do all the internal file handling for you, but you won't get any immediate results.


PathIE supports the extraction of special keywords on the dependency path of sentences. 
For more information, see the section below.

## Consider Sections (Full-text documents)
To extract statements from sections in documents, the _--section_ parameter must be set.
```
python src/kgextractiontoolbox/extaction/pipeline.py --extraction_type METHOD --collection COLLECTION --sections
```
Note that this parameter must also be set when running the extraction methods separately (not in pipeline mode). 
Every script below supports the _--section_ parameter.

## Running the Extraction Methods
If you want to work with the immediate results, you can invoke the extraction methods manually. 
The following section describes this process. 
In contrast to the previous pipeline, you have to insert your results manually into the database for later data cleaning.
Note, that there is no checking if a document has already been processed by the toolbox.
### Running PathIE
PathIE needs an annotated document file. 
All sentences that do not have at least two entity mentions won't be processed by PathIE.
Make sure that your document file contains entity annotations (tags).

Run PathIE:
```
python src/kgextractiontoolbox/extraction/pathie/main.py INPUT_DOC OUTPUT_PATHIE
```

PathIE supports the extraction of special keywords on the dependency path of sentences. 
Therefore, you need to design a relation vocabulary, see [Cleaning Readme](README_04_CLEANING.md).
You may use a relation vocabulary for additional keywords on the Path:
```
python src/kgextractiontoolbox/extraction/pathie/main.py INPUT_DOC OUTPUT_PATHIE --relation_vocab RELATION.json
```

As an example, you may specify the following relation vocabulary:
```
{
  "born": [
    "bear",
    "birthplace",
    "birthplace"
  ],
  "elect": [
    "elect*", 
    "*election",
    "presidential elect*"
  ]
}
```
This vocabulary will enforce PathIE to extract statements between entities, if an entry of the vocabulary such as election, birthplace etc. is mentioned.
Wildcards (*) are allowed in the beginning or ending of an entry (due to performance). 
An entry might also contain a white space. 
### Running PathIE Stanza
Stanza is not installed by default. To use it, please install:
```
pip install stanza~=1.2.3
```


Before working with Stanza, you need to setup the English model. 
Therefore, run:
```
python src/kgextractiontoolbox/setup_stanza.py
```
This may take a while.

PathIE needs an annotated document file. 
All sentences that do not have at least two entity mentions won't be processed by PathIE.
Make sure that your document file contains entity annotations (tags).
Run PathIE Stanza:
```
python src/kgextractiontoolbox/extraction/pathie_stanza/main.py INPUT_DOC OUTPUT_PATHIE
```

PathIE supports the extraction of special keywords on the dependency path of sentences. 
For more information, see the section above.
```
python src/kgextractiontoolbox/extraction/pathie_stanza/main.py INPUT_DOC OUTPUT_PATHIE --relation_vocab RELATION.json
```


You can force Stanza to run in CPU mode by using the **--cpu** flag.
```
python src/kgextractiontoolbox/extraction/pathie_stanza/main.py INPUT_DOC OUTPUT_PATHIE --CPU --relation_vocab RELATION.json
```

### PathIE Output Format
The following section shows some PathIE example files. Note, that PathIE do not mirror the extractions in its output.
If you use the output in your application, you might have to mirror (swap subject and object)
 the extractions. 
PathIE outputs directly include entity information because its used directly in the extraction phase.

Example:

|document id|subject id|subject str|subject type|predicate|predicate lemmatized|object id|object str|object type|confidence|sentence                                                                                                                                                            |
|-----------|----------|-----------|------------|---------|--------------------|---------|----------|-----------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|100        |Q4        |hamburg    |Location    |born     |bear                |Q2       |merkel    |Person     |1.0       |Merkel was born in [...]|
|100        |Q4        |hamburg    |Location    |born     |bear                |germany  |germany   |GPE        |1.0       |Merkel was born in [...]|
|100        |Q2        |merkel     |Person      |born     |bear                |germany  |germany   |GPE        |1.0       |Merkel was born in [...]|
|102        |Q5        |americas   |Location    |cover    |cover               |earth    |earth     |LOC        |0.5       |Along [...]                                           |


A biomedical example might look like:

|document id| subject id                    |subject str|subject type                                      |predicate|lemmatized predicate|object id|object str  |object type| confidence | sentence|
|-------|-----------------------------|-------------------|---------------------------------------------|-------|------|-------|------------|--------|-------------------|----------------------------------------------------------------------------------------------------------------------------------|
|7121659|D058186                      |acute renal failure|Disease                                      |induced|induce|D012293|rifampicin  |Chemical|0.4 |5 patients [...]|
|7121659|D012293                      |rifampicin         |Chemical                                     |induced|induce|D013921|thrombopenia|Disease |0.4 |5 patients  [...]|
|23952588|D010300                      |Parkinson's disease|Disease                                      |induced|induce|D007980|levodopa    |Chemical|0.2|Risk factors  [...] |
|23952588|D004409                      |dyskinesia         |Disease                                      |leads  |lead  |D007980|levodopa    |Chemical|0.5                |Chronic pulsatile[...]    |

As a TSV file:
```
document id	subject id	 subject str	subject type	predicate	predicate lemmatized	object id	object str	object type	confidence	sentence
7121659	D058186	acute renal failure	Disease	induced	induce	D012293	rifampicin	Chemical	0.4	5 patients with acute renal failure (3 with thrombopenia and hemolysis) induced by the reintroduction of rifampicin are described.
7121659	D012293	rifampicin	Chemical	induced	induce	D013921	thrombopenia	Disease	0.4	5 patients with acute renal failure (3 with thrombopenia and hemolysis) induced by the reintroduction of rifampicin are described.
23952588	D010300	Parkinson's disease	Disease	induced	induce	D007980	levodopa	Chemical	0.2	Risk factors and predictors of levodopa-induced dyskinesia among multiethnic Malaysians with Parkinson's disease.
23952588	D004409	dyskinesia	Disease	leads	lead	D007980	levodopa	Chemical	0.5	Chronic pulsatile levodopa therapy for Parkinson's disease (PD) leads to the development of motor fluctuations and dyskinesia.
```


### Loading PathIE
You can load the PathIE files by running:
```
python src/kgextractiontoolbox/extraction/loading/load_pathie_extractions.py PATHIE.tsv --collection COLLECTION --extraction_type PathIE
```
If you do not want to mirror (swap subject and object) the PathIE extractions, use **--not_symmetric**:
```
python src/kgextractiontoolbox/extraction/loading/load_pathie_extractions.py PATHIE.tsv --collection COLLECTION --extraction_type PathIE --not_symmetric
```

Supported extraction types: PathIE and PathIEStanza

### Running OpenIE
You can run OpenIE directly by:
```
python src/kgextractiontoolbox/extraction/openie/main.py INPUT_DOCUMENT OUTPUT
```
If the input file has no annotations, please disable the entity filter for sentences by:
```
python src/kgextractiontoolbox/extraction/openie/main.py INPUT_DOCUMENT OUTPUT --no_entity_filter
```

### Running OpenIE 5.1
You can run OpenIE 5.1 directly by:
```
python src/kgextractiontoolbox/extraction/openie51/main.py INPUT_DOCUMENT OUTPUT
```
If the input file has no annotations, please disable the entity filter for sentences by:
```
python src/kgextractiontoolbox/extraction/openie51/main.py INPUT_DOCUMENT OUTPUT --no_entity_filter
```


### Running OpenIE6
You can run OpenIE6 directly by:
```
python src/kgextractiontoolbox/extraction/openie6/main.py INPUT_DOCUMENT OUTPUT
```
If the input file has no annotations, please disable the entity filter for sentences by:
```
python src/kgextractiontoolbox/extraction/openie6/main.py INPUT_DOCUMENT OUTPUT --no_entity_filter
```

## OpenIE Output Format
Here, unlike in PathIE, no entity information is available because OpenIE tools produce their output first and these outputs will then be cleaned in our toolbox.

Example:

|document id|subject                                                |predicate                |predicate lemmatized |object                                                                                      |confidence|sentence                                                                                                                                                                                                                                                                                               |
|-----------|-------------------------------------------------------|-------------------------|---------------------|--------------------------------------------------------------------------------------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|100        |100. Merkel                                            | was born                |  be bear            | in Hamburg in then-West Germany                                                          |0.42      |Merkel [...]                                                                                                                                    |
|100        |her father,                                            | received                |  receive            | a pastorate in Perleberg.                                                                |0.38      |Merkel [...]                                                                                                                                     |
|100        |100. Merkel                                            | moving                  |  move               | to East Germany as an infant her father, a Lutheran clergyman, a pastorate                |0.18      |Merkel [...]                                                                                                                                     |
|100        |Merkel                                                 | entered politics serving|  enter politic serve| as deputy spokesperson for the first democratically elected East German Government briefly|0.90      |She obtained [...]|
|100        |the first democratically elected East German Government| led                     |  lead               | by Lothar de Maizière.                                                                |0.72      |She obtained [...]|
|100        |She                                                    | worked                  |  work               | as a research scientist until 1989.[14]                                                   |0.63      |She obtained [...]|


As a TSV file:
```
document id	subject	predicate	predicate lemmatized	object	confidence	sentence
100	100. Merkel	 was born	  be bear	 in Hamburg in then-West Germany,)	0.42	Merkel was born in Hamburg in then-West Germany, moving to East Germany as an infant when her father, a Lutheran clergyman, received a pastorate in Perleberg..
100	her father,	 received	  receive	 a pastorate in Perleberg..)	0.38	Merkel was born in Hamburg in then-West Germany, moving to East Germany as an infant when her father, a Lutheran clergyman, received a pastorate in Perleberg..
100	100. Merkel	 moving	  move	 to East Germany as an infant her father, a Lutheran clergyman, a pastorate)	0.18	Merkel was born in Hamburg in then-West Germany, moving to East Germany as an infant when her father, a Lutheran clergyman, received a pastorate in Perleberg..
100	Merkel	 entered politics serving	  enter politic serve	 as deputy spokesperson for the first democratically elected East German Government briefly)	0.90	She obtained a doctorate in quantum chemistry in 1986 and worked as a research scientist until 1989.[14] Merkel entered politics in the wake of the Revolutions of 1989, briefly serving as deputy spokesperson for the first democratically elected East German Government led by Lothar de Maizière..
100	the first democratically elected East German Government	 led	  lead	 by Lothar de Maizière..)	0.72	She obtained a doctorate in quantum chemistry in 1986 and worked as a research scientist until 1989.[14] Merkel entered politics in the wake of the Revolutions of 1989, briefly serving as deputy spokesperson for the first democratically elected East German Government led by Lothar de Maizière..
100	She	 worked	  work	 as a research scientist until 1989.[14])	0.63	She obtained a doctorate in quantum chemistry in 1986 and worked as a research scientist until 1989.[14] Merkel entered politics in the wake of the Revolutions of 1989, briefly serving as deputy spokesperson for the first democratically elected East German Government led by Lothar de Maizière..
```


Another biomedical example:

|document id|subject str     |predicate|lemmatized predicate                                    |object str|confidence |sentence|
|--------|-----------------------------|----------|---------------------------------------------|----------|------|----------------------------------------------------------------------------------------------|
|22836123|onset scleroderma renal crisis|induced by|induce by                                    |tacrolimus|1.000 |Late [...]|
|22836123|crisis                       |is rare   |be rare                                      |sclerosis |1.000 |Scleroderma [...]|
|22836123|moderate                     |is recognized as|be recognize as                              |major risk factor|1.000 |Moderate [...] |
|22836123|have reports                 |precipitated by|precipitate by                               |cyclosporine patients|1.000 |Furthermore , there [...]|


The biomedical example as a tsv file:
```
document id	subject	predicate	predicate lemmatized	object	confidence	sentence
22836123	onset scleroderma renal crisis	induced by	induce by	tacrolimus	1.000	Late - onset scleroderma renal crisis induced by tacrolimus and prednisolone : a case report .
22836123	crisis	is rare	be rare	sclerosis	1.000	Scleroderma renal crisis ( SRC ) is a rare complication of systemic sclerosis ( SSc ) but can be severe enough to require temporary or permanent renal replacement therapy .
22836123	moderate	is recognized as	be recognize as	major risk factor	1.000	Moderate to high dose corticosteroid use is recognized as a major risk factor for SRC .
22836123	have reports	precipitated by	precipitate by	cyclosporine patients	1.000	Furthermore , there have been reports of thrombotic microangiopathy precipitated by cyclosporine in patients with SSc .
```

## Loading OpenIE outputs
If the OpenIE should be cleaned by our toolbox, the data must be loaded into our database.
To apply OpenIE entity-based filtering, the document content plus annotations must be loaded into the database.
If the documents are already inserted, load the OpenIE extractions by:
```
python src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py OPENIE_OUTPUT --collection DOCUMENT_COLLECTION --extraction_type OpenIE
```
By default, OpenIE arguments (subjects and objects) will be filtered by the partial entity filter. We support the following options:
- no_entity_filter (does not apply any filtering)
- partial_entity_filter (partial entity mention in an argument is sufficient)
- exact_entity_filter (OpenIE argument must match an entity exactly)

You can specify the filtering method by the *--entity_filter* argument:
```
python src/kgextractiontoolbox/extraction/loading/load_openie_extractions.py OPENIE_OUTPUT --entity_filter partial_entity_filter  --collection DOCUMENT_COLLECTION --extraction_type OpenIE
```

We support the following filter options:
- no_entity_filter (do not filter OpenIE methods)
- partial_entity_filter (Default; force that in subject and object an entity must partially be included)
- exact_entity_filter (force that subject and object must match an entity)
- only_subject_exact (force that subject must match an entity)


The extraction type will be stored in the database (Predication table). Usually select on of these OpenIE, OpenIE51 and OpenIE6 names.

We support the following optional flags:
- --filter_predicate_str (Should the predicate be filtered to retain only verb phrases?)
- --swap_passive_voice  (Swap passive voice to active voice)
- --ignore_be_and_have (Ignore be and have verb phrases)
- --keep_original_predicate (The original predicate is kept without further cleaning or lemmatizing)
