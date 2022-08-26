# Text Classification
The toolbox supports the classification of texts by regular expressions. 
Therefore, we apply a simple search whether a regular expression can be found within a document's text.
If the expression can be matched, we classify the document as belonging to the specified class.

```
python3 src/kgextractiontoolbox/entitylinking/classification.py -c COLLECTION -r EXPRESSION_FILE --cls CLASS -w 15
```

If documents are not present in the database, the script will automatically load them. 
Again, you can specify the **--skip-load** argument to skip loading.

Arguments:
- **COLLECTION**: specifies the document collection
- **EXPRESSION_FILE**: path to a .txt file with regular expressions
- **CLS**: document class if one rule is matched
- **w**: number of parallel works


## Classification File
Regular expressions must be stored as a .txt file. 
Each line represents a regular expression.
We support the following notation:
- \* as the known wildcard operation
- AND to force that two expressions must be matched within a text (Either both or no match)
- w/1, w/2, ... to allow an arbitrary number of words between two expressions

Note that we do not support more advanced expressions for now (due to complexity and performance).

A pharmaceutical example file is shown below:

```
Saponin*
Terpen*
Traditional Knowledge
Traditional w/1 Medicine
Triterpen*
Unani
volatile w/1 compound*
target* AND thera*
target* AND molec*
```

Document classifications can be exported via the export script as a JSON (see export readme).