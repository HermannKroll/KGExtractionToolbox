from unittest import TestCase

from spacy.lang.en import English

from kgextractiontoolbox.extraction.cosentences.main import extract_based_on_co_occurrences_in_sentences


class COSentenceExtractionTest(TestCase):

    def setUp(self):
        self.spacy_nlp = English()  # just the language with no model
        self.spacy_nlp.add_pipe("sentencizer")

        self.doc1_content = """
        {
              "id": 1,
              "title": "This is an article about nanoparticles, antioxidant and copper.",
              "abstract": "",
              "tags": [
                {
                  "id": "MESH:D053758",
                  "mention": "nanoparticles",
                  "start": 26,
                  "end": 38,
                  "type": "DosageForm"
                },
                {
                  "id": "Antioxidants",
                  "mention": "antioxidant",
                  "start": 41,
                  "end": 51,
                  "type": "Excipient"
                },
                {
                  "id": "CHEMBL55643",
                  "mention": "copper",
                  "start": 56,
                  "end": 62,
                  "type": "Chemical"
                }
            ]
        }            
        """

        self.doc2_content = """
        {
              "id": 1,
              "title": "This is an article about nanoparticles. Antioxidant and copper are also important",
              "abstract": "",
              "tags": [
                {
                  "id": "MESH:D053758",
                  "mention": "nanoparticles",
                  "start": 26,
                  "end": 38,
                  "type": "DosageForm"
                },
                {
                  "id": "Antioxidants",
                  "mention": "antioxidant",
                  "start": 41,
                  "end": 51,
                  "type": "Excipient"
                },
                {
                  "id": "CHEMBL55643",
                  "mention": "copper",
                  "start": 56,
                  "end": 62,
                  "type": "Chemical"
                }
            ]
        }            
        """

        self.doc3_content = """
        {
              "id": 1,
              "title": "This is an article about nanoparticles. Antioxidant and copper are also important",
              "abstract": "",
              "tags": [
               {
                  "id": "This",
                  "mention": "this",
                  "start": 1,
                  "end": 4,
                  "type": "DosageForm"
                },
                {
                  "id": "MESH:D053758",
                  "mention": "nanoparticles",
                  "start": 26,
                  "end": 38,
                  "type": "DosageForm"
                },
                {
                  "id": "Antioxidants",
                  "mention": "antioxidant",
                  "start": 41,
                  "end": 51,
                  "type": "Excipient"
                },
                {
                  "id": "CHEMBL55643",
                  "mention": "copper",
                  "start": 56,
                  "end": 62,
                  "type": "Chemical"
                }
            ]
        }            
        """

    def test_extract_based_on_co_occurrences_in_sentences(self):
        d1_tuples = extract_based_on_co_occurrences_in_sentences(self.spacy_nlp, self.doc1_content)
        self.assertEqual(3, len(d1_tuples))
        pairs = {(t.subject_id, t.object_id) for t in d1_tuples}

        self.assertIn(("MESH:D053758", "Antioxidants"), pairs)
        self.assertIn(("MESH:D053758", "CHEMBL55643"), pairs)
        self.assertIn(("Antioxidants", "CHEMBL55643"), pairs)

        d2_tuples = extract_based_on_co_occurrences_in_sentences(self.spacy_nlp, self.doc2_content)
        self.assertEqual(1, len(d2_tuples))
        pairs = {(t.subject_id, t.object_id) for t in d2_tuples}

        self.assertIn(("Antioxidants", "CHEMBL55643"), pairs)

        d3_tuples = extract_based_on_co_occurrences_in_sentences(self.spacy_nlp, self.doc3_content)
        self.assertEqual(2, len(d3_tuples))
        pairs = {(t.subject_id, t.object_id) for t in d3_tuples}
        self.assertIn(("This", "MESH:D053758"), pairs)
        self.assertIn(("Antioxidants", "CHEMBL55643"), pairs)
