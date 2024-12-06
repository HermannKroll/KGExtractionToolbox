# Export
This Readme contains instructions on how to export data from our toolbox database.


# Annotation Export
First, the entity linking annotations can be exported in two formats: JSON and PubTator.
You can export the annotations via:
```
python src/kgextractiontoolbox/document/export.py -d -t EXPORT_FILE --format JSON --collection COLLECTION
```
You can export only tags (only -t) or document contents and tags (-d and -t).
You can export a whole document collection or a set of document ids in that collection.
See the help for more information.


The export file will look like:

JSON (only tags):
```
[
   {
     "id": 100,
     "tags": [
      {
       "id": "Q2",
       "mention": "merkel",
       "start": 14,
       "end": 20,
       "type": "Person"
      },
      {
       "id": "Q4",
       "mention": "hamburg",
       "start": 33,
       "end": 40,
       "type": "Location"
      }
     ]
   }
]
```

JSON (tags + content):
```
[
   {
     "id": 100,
     "title": "Angela Merkel",
     "abstract": "Merkel was born in Hamburg in then-West Germany, moving [...].
     "tags": [
      {
       "id": "Q2",
       "mention": "merkel",
       "start": 14,
       "end": 20,
       "type": "Person"
      },
      {
       "id": "Q4",
       "mention": "hamburg",
       "start": 33,
       "end": 40,
       "type": "Location"
      }
     ],
     "sections": [
      {
       "position": 0, 
       "title": "Introduction", 
       "text": "Angela Dorothea Merkel is a retired German politician and scientist [...]"
      }, 
      {
       "position": 1, 
       "title": "Background and early life", 
       "text": "Merkel was born Angela Dorothea Kasner in 1954, in Hamburg, West Germany [...]"
      }
     ]
   }
]
```
The "sections" part is optional.

PubTator (only Tags) is a TSV file. Each line contains:
- document id
- start position
- end position
- entity id
- entity type
- entity mention (string in text)

Values are seperated by a *\t*
```
100	14	20	merkel	Person	Q2
100	33	40	hamburg	Location	Q4
100	222	226	1986	DATE	1986
100	268	272	1989	DATE	1989
100	278	284	merkel	Person	Q2
100	508	514	merkel	Person	Q2
100	628	634	merkel	Person	Q2
100	829	835	merkel	Person	Q2
```
PubTator (tags + document content):
```
100|t|Angela Merkel
100|a|Merkel was born in Hamburg in then-West Germany, moving [...].
100	14	20	merkel	Person	Q2
100	33	40	hamburg	Location	Q4
100	222	226	1986	DATE	1986
100	268	272	1989	DATE	1989
100	278	284	merkel	Person	Q2
100	508	514	merkel	Person	Q2
100	628	634	merkel	Person	Q2
100	829	835	merkel	Person	Q2
```
As described in the classification README, document classifications can be included in the export using the `--classification` flag:
```
python src/kgextractiontoolbox/document/export.py -d -t EXPORT_FILE --format JSON --collection COLLECTION --classification
```



# NarrativeDocument Export
To export all documents from the database in JSON format, a corresponding script exists.
A collection can be passed as a parameter to specify the respective document collection to export.

Export documents in a single file by running:
```
python src/kgextractiontoolbox/extraction/export_narrative_documents.py OUTPUT --collection COLLECTION [--sqllog]
```
- `OUTPUT` specifies the target location and filename of the exported documents.
- `COLLECTION` specifies the document collection or if not provided every document collection present.
- `--sqllog` enables logging of the SQL commands executed.

An example export could look like.
```json
[
  {
    "id": 1496277,
    "title": "[Rhabdomyolysis due to simvastin. Apropos of a case with review of the literature].",
    "abstract": "A new case of simvastatin-induced acute rhabdomyolysis with heart failure after initiation of treatment with fusidic acid is reported. In most reported instances, statin treatment was initially well tolerated with muscle toxicity developing only after addition of another drug. The mechanism of this muscle toxicity is unelucidated but involvement of a decrease in tissue Co enzyme Q is strongly suspected.",
    "classification": {
      "Pharmaceutical": "drug:drug(356, 360);toxi*:toxicity(305, 313)"
    },
    "tags": [
      {
        "id": "MESH:D012206",
        "mention": "rhabdomyolysis",
        "start": 1,
        "end": 15,
        "type": "Disease"
      },
      ...
    ],
    "metadata": {
      "publication_year": 1992,
      "publication_month": 4,
      "authors": "Dromer, C | Vedrenne, C | Billey, T | Pages, M | Fourni\u00e9, B | Fourni\u00e9, A",
      "journals": "Revue du rhumatisme et des maladies osteo-articulaires, Vol. 59 No. 4 (Apr 1992)",
      "doi": "https://www.pubpharm.de/vufind/Search/Results?lookfor=NLM1496277"
    },
    "sentences": [
      {
        "id": 2456018,
        "text": "A new case of simvastatin-induced acute rhabdomyolysis with heart failure after initiation of treatment with fusidic acid is reported."
      },
      ...
    ],
    "statements": [
      {
        "subject_id": "CHEMBL374975",
        "subject_type": "Drug",
        "subject_str": "fusidic acid",
        "predicate": "treatment",
        "relation": "treats",
        "object_id": "MESH:D006333",
        "object_type": "Disease",
        "object_str": "heart failure",
        "sentence_id": 2456018
      },
      ...
    ]
  }, ...
]
```

Please note, that the document collection of the document is not part of the output and therefore cannot be restored automatically.

# Statement Export
Finally, you may want to export the statement extractions from our database. 
We assume in the following that you have already done the extraction and cleaning.

Export statements by running:
```
python src/kgextractiontoolbox/extraction/export_predications.py OUTPUT --collection COLLECTION --format TSV
```

We support the following options to export predications:
- TSV (with or without metadata)
- RDF (with or without metadata)

To enable the export of metadata, please add the **--metadata** argument.
Export statements by running:
```
python src/kgextractiontoolbox/extraction/export_predications.py OUTPUT --collection COLLECTION --format TSV --metadata
```

In addition, the toolbox does not export statements that have a **None** relation.
You can enable this export by using the **--none_relations** argument:
```
python src/kgextractiontoolbox/extraction/export_predications.py OUTPUT --collection COLLECTION --format TSV --none_relations
```

*RDF*. Please note that we do not set a custom namespace here. 
If you want to work with namespaces, then you can define your entity ids with namespaces.

Example exports are shown below.


## Export without Metadata

Example:

|subject_id|relation                                               |object_id                |
|----------|-------------------------------------------------------|-------------------------|
|Q1        |born                                                   |Q3                       |
|Q2        |born                                                   |Q4                       |
|Q1        |born                                                   |Q3                       |
|Q2        |born                                                   |Q4                       |


### As TSV File
```
subject_id	relation	object_id
Q1	born	Q3
Q2	born	Q4
Q1	born	Q3
Q2	born	Q4

```

### As RDF Turtle Format (ttl)
```
Q2> <born> <Q4> .

<Q1> <born> <Q3> .
```

## Export with Metadata

Example:

|document_id|document_collection                                    |subject_id               |subject_type|subject_str|predicate|relation|object_id|object_type|object_str|sentence_id|extraction_type|FIELD13|FIELD14|FIELD15 |FIELD16|FIELD17|FIELD18|FIELD19|FIELD20|FIELD21|FIELD22|FIELD23|FIELD24|FIELD25|FIELD26|FIELD27|FIELD28|FIELD29|FIELD30|FIELD31|FIELD32|FIELD33|FIELD34 |FIELD35  |FIELD36|FIELD37 |FIELD38|FIELD39  |FIELD40|FIELD41  |FIELD42|FIELD43|
|-----------|-------------------------------------------------------|-------------------------|------------|-----------|---------|--------|---------|-----------|----------|-----------|---------------|-------|-------|--------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|--------|---------|-------|--------|-------|---------|-------|---------|-------|-------|
|101        |wikipedia                                              |Q1                       |Person      |obama      |bear     |born    |Q3       |Location   |honolulu  |Obama      |was            |born   |in     |Honolulu|,      |Hawaii |.      |OpenIE |       |       |       |       |       |       |       |       |       |       |       |       |       |       |        |         |       |        |       |         |       |         |       |       |
|100        |wikipedia                                              |Q2                       |Person      |merkel     |bear     |born    |Q4       |Location   |hamburg   |Merkel     |was            |born   |in     |Hamburg |in     |then   |-      |West   |Germany|,      |moving |to     |East   |Germany|as     |an     |infant |when   |her    |father |,      |a      |Lutheran|clergyman|,      |received|a      |pastorate|in     |Perleberg|.      |OpenIE |
|101        |wikipedia                                              |Q1                       |Person      |obama      |bear     |born    |Q3       |Location   |honolulu  |Obama      |was            |born   |in     |Honolulu|,      |Hawaii |.      |OpenIE |       |       |       |       |       |       |       |       |       |       |       |       |       |       |        |         |       |        |       |         |       |         |       |       |
|100        |wikipedia                                              |Q2                       |Person      |merkel     |bear     |born    |Q4       |Location   |hamburg   |Merkel     |was            |born   |in     |Hamburg |in     |then   |-      |West   |Germany|,      |moving |to     |East   |Germany|as     |an     |infant |when   |her    |father |,      |a      |Lutheran|clergyman|,      |received|a      |pastorate|in     |Perleberg|.      |OpenIE |

### As TSV File
```
document_id document_collection    subject_id subject_type   subject_str    predicate  relation   object_id  object_type    object_str sentence_id    extraction_type
101    wikipedia  Q1 Person obama  bear   born   Q3 Location   honolulu   Obama was born in Honolulu , Hawaii .  OpenIE
100    wikipedia  Q2 Person merkel bear   born   Q4 Location   hamburg    Merkel was born in Hamburg in then - West Germany , moving to East Germany as an infant when her father , a Lutheran clergyman , received a pastorate in Perleberg .   OpenIE
101    wikipedia  Q1 Person obama  bear   born   Q3 Location   honolulu   Obama was born in Honolulu , Hawaii .  OpenIE
100    wikipedia  Q2 Person merkel bear   born   Q4 Location   hamburg    Merkel was born in Hamburg in then - West Germany , moving to East Germany as an infant when her father , a Lutheran clergyman , received a pastorate in Perleberg .   OpenIE
```

### As RDF Turtle Format (ttl)
```
<sentence_id_21> <text> "Merkel was born in Hamburg in then - West Germany , moving to East Germany as an infant when her father , a Lutheran clergyman , received a pastorate in Perleberg ." .

<sentence_id_23> <text> "Obama was born in Honolulu , Hawaii ." .

<statement_32> <document_collection> <wikipedia> ;
    <document_id> <100> ;
    <extraction_type> "OpenIE" ;
    <object_id> <Q4> ;
    <object_str> "hamburg" ;
    <object_type> <Location> ;
    <predicate> "bear" ;
    <relation> "born" ;
    <sentence_id> "sentence_id_21" ;
    <subject_id> <Q2> ;
    <subject_str> "merkel" ;
    <subject_type> <Person> .

<statement_33> <document_collection> <wikipedia> ;
    <document_id> <101> ;
    <extraction_type> "OpenIE" ;
    <object_id> <Q3> ;
    <object_str> "honolulu" ;
    <object_type> <Location> ;
    <predicate> "bear" ;
    <relation> "born" ;
    <sentence_id> "sentence_id_23" ;
    <subject_id> <Q1> ;
    <subject_str> "obama" ;
    <subject_type> <Person> .
```