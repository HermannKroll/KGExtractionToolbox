# Cleaning
The core idea of our toolbox is to rely on unsupervised extraction methods which will produce noise outputs. 
The following methods are designed to clean the noisy extractions to retain precise semantics.
The cleaning package consists of:
- predicate unification: clean synonymous predicates
- type constraint filtering: remove statements that hurt type constraints



# Building a Relation Vocabulary:
The first step towards building a relation vocabulary is to get an overview about the extracted predicates.
Therefore, you can run the following script:
```
python src/kgextractiontoolbox/cleaning/export_predicate_mappings.py
```

This script will produce a TSV file of predicates, the number of occurrences and the relation to which the predicates are currently mapped. 
If you run the script for the first time, all predicates will be mapped to the relation None (do not have a mapping yet).

```
predicate   count  relation
bear   6  None
elect over 4  None
appoint follow 2  None
cover  2  None
lead cdu   2  None
serve  2  None
succeed    2  None
```

As a table:

|predicate|count                                                  |relation                 |
|---------|-------------------------------------------------------|-------------------------|
|bear     |6                                                      |None                     |
|elect over|4                                                      |None                     |
|appoint follow|2                                                      |None                     |
|cover    |2                                                      |None                     |
|lead cdu  |2                                                      |None                     |
|serve    |2                                                      |None                     |
|succeed  |2                                                      |None                     |


After exporting the predicate mapping, you can start to build your own relation vocabulary as a JSON file.

A relation vocabulary is defined in a JSON file. A key represents the relation and a list of synonyms can be specified as its values.
In addition to standard strings, we support the usage of wildcards in the beginning or ending of an entry:
- strings starting with a wildcard (all predicates ending with this string will be mapped to it)
- string ending with a wildcard (all predicates starting with this string will be mapped to it)
```
{
  "born": [
    "bear"
  ],
  "elect": [
    "elect*", 
    "*election"
  ]
}
```

Then, unify the predicates in the database by running:
```
python src/kgextractiontoolbox/cleaning/canonicalize_predicates.py --relation_vocab RELATION_VOCAB.json
```
You can also integrate a fasttext word embedding into the canonicalizing procedure. 
However, this will require a pre-trained model.
You may download a pre-trained wikipedia model from fasttext ([Link](https://fasttext.cc/docs/en/pretrained-vectors.html)).
For example: English, Bin+Text [Link](https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.en.zip).
Attention: Our toolbox requires a .bin word2vec model file. We do not support other formats.

If you are working in specific domain, then it might be useful to use a domain-specific word embedding such as a [biomedical word embedding](https://github.com/ncbi-nlp/BioSentVec).
```
python src/kgextractiontoolbox/cleaning/canonicalize_predicates.py --relation_vocab RELATION_VOCAB.json --word2vec_model PATH
```



Next, run the export of predicate mappings again:
```
python src/kgextractiontoolbox/cleaning/export_predicate_mappings.py MAPPING.tsv
```


You will hopefully see the results. Some predicates will be mapped to the corresponding relation.
```
predicate   count  relation
bear   6  born
elect over 4  elect
appoint follow 2  None
cover  2  None
lead cdu   2  None
serve  2  None
succeed    2  None
```

As a table:

|predicate|count                                                  |relation                 |
|---------|-------------------------------------------------------|-------------------------|
|bear     |6                                                      |born                     |
|elect over|4                                                      |elect                    |
|appoint follow|2                                                      |None                     |
****

Both methods support the document collection argument
```
--collection COLLECTION
```
Then, only statements that are extracted from the corresponding document collection will be considered.

If you are happy with the results, you can move on to the next step. 
If you would like to edit your relation vocabulary, go back to the first step and iterate over and over again. 



# Relation Type Constraints
Finally, you may clean your extraction by formulating type constraints. 
The relation **born** could be a relation between persons and locations only. 
Type constraints can be formulated in an JSON file in the following format:
```
{
  "born": {
    "subjects": [
      "Person"
    ],
    "objects": [
      "Location"
    ]
  }
}
```
Note, subjects and objects can be lists, e.g., "Location", "City", ...

Apply the cleaning by running the following script:

```
python src/kgextractiontoolbox/cleaning/check_type_constraints.py.py TYPE_CONSTRAINTS.json --allow_reorder
```
If the argument **allow_reorder** is set, tuples that hurt the type constraints will be flipped, if the flipping would solve the problem:
For example, the tuple (Location, born, Person) will be flipped to (Person, born, Location).
You may want to use this parameter when working with *OpenIE*. 
If you work with *PathIE* and already have mirrored facts (because of the symmetric extraction), a reordering is useless.

You may want to apply the relation type constraints to a single document collection only:
```
python src/kgextractiontoolbox/cleaning/check_type_constraints.py.py TYPE_CONSTRAINTS.json --collection COLLECTION --allow_reorder
```


# Biomedical Examples:
As a complex example, our biomedical relation vocabulary is defined as:
```
{
  "administered": [
    "receiv*",
    "administrat*"
  ],
  "induces": [
    "stimulat*",
    "increas*",
    "activat*"
  ],
  "interacts": [
    "bind",
    "interact*",
    "target*",
    "regulat*",
    "block*"
  ],
  "metabolises": [
    "metabol*"
  ],
  "inhibits": [
    "disrupt*",
    "suppres*",
    "inhibit*",
    "disturb*"
  ],
  "treats": [
    "prevent*",
    "use",
    "improv*",
    "promot*",
    "sensiti*",
    "aid",
    "treat*",
    "*therap*"
  ]
}
```

As an example, here is our biomedical constraint file:
```
{
  "treats": {
    "subjects": [
      "Chemical",
      "Drug",
      "Excipient",
      "PlantFamily"
    ],
    "objects": [
      "Disease",
      "Species"
    ]
  },
  "administered": {
    "subjects": [
      "DosageForm",
      "Method",
      "LabMethod"
    ],
    "objects": [
      "All"
    ]
  },
  "method": {
    "subjects": [
      "Method",
      "LabMethod"
    ],
    "objects": [
      "All"
    ]
  },
  "inhibits": {
    "subjects": [
      "Chemical",
      "Drug",
      "Excipient",
      "PlantFamily"
    ],
    "objects": [
      "Gene"
    ]
  }
}
```