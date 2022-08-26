

# Supported Document Formats

Our Pipeline supports a JSON document format. 
Every document is identified via an unique id (integer). 
Documents must belong to a document collection, but each document id must be unique within the collection.



## Loading Documents
You can load your documents:
```
python src/kgextractiontoolbox/documents/load_document.py DOCUMENTS.json --collection COLLECTION
```
Document ids must be unique integers within a document collection. 
The loading procedure will automatically include entity annotations (tags) if contained in the document file. 
If you don't want to include tags, use the **--ignore_tags** argument.

```
python src/kgextractiontoolbox/documents/load_document.py DOCUMENTS.json --collection COLLECTION --ignore_tags
```

A document file may contain only annotations (exported by our toolbox; see [export](README_04_EXPORT.md)).
The toolbox will only load these annotations if the corresponding documents with titles or abstracts have been inserted into the database.


### Document JSON Format
Here is an example of our JSON format:
```
[
  {
      "id": 12345,
      "title": "Barack Obama [...]",
      "abstract": "Obama was born in Honolulu, Hawaii. After graduating from Columbia University in 1983 [..]",
      "sections": [
       {
        "position": 0, 
        "title": "Introduction", 
        "text": "Barack Hussein Obama II is an American politician [...]"
       }, 
       {
        "position": 1, 
        "title": "Early life and career", 
        "text": "Obama was born on August 4, 1961, at Kapiolani Medical Center for Women and Children [...]"
       }
      ]
  },
  // more documents ...
]
```
The "sections" part is optional. The outmost array brackets `[]` can be omitted if only a single json document should be contained within the file.

Note:
- a document id must be an integer
- id, title and abstracts are required

### Document PubTator Format
The second document format is the so-called [PubTator format](https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/PubTator/tutorial/index.html). 
A PubTator document has a document id, a document collection, a title and an abstract. 
```
document_id|t|title text here
document_id|a|abstract text here

```
ATTENTION: the PubTator file must end with two *\n* characters. 
The document id must be an integer. Title and abstract can include special characters - the texts will be sanitized in our pipeline. 
If you want to tag several documents, you can choose from two options:
1. Create a PubTator file for each document and put them into a directory
2. Create a single PubTator file with several documents
```
document_id_1|t|title text here
document_id_1|a|abstract text here

document_id_2|t|title text here
document_id_2|a|abstract text here

document_id_3|t|title text here
document_id_3|a|abstract text here

```
The files are separated by two new line characters *\\n*. ATTENTION: the PubTator file must end with two *\\n* characters. 


### Expert Loading for Custom Tagging
The following is only of interest, if you are working with custom taggers.
In addition, you can specify a tagger map when loading a document file. 
Then, the database will store the information that these files have been processed by the corresponding taggers.
This is useful, if you work with custom taggers, and you don't want to annotate document twice.
As an example:
```
{
  "Chemical" : ["TaggerOne", "0.2.1"],
  "Disease" : ["TaggerOne", "0.2.1"],
  "DosageForm": ["DosageFormTagger" , "1.0.0"],
  "Gene" : ["GNormPlus", "unknown"],
  "Species" : ["SR4GN", "unknown" ],
  "CellLine" : ["TaggerOne", "0.2.1"],
  "Variant" : [ "tmVar", "2.0"]
}
```
Then, run
```
python src/kgextractiontoolbox/documents/load_document.py DOCUMENTS.json --tagger_map TAGGER_MAP.json --collection COLLECTION
```