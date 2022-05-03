import json
import copy
import unittest
from kgextractiontoolbox.backend.retrieve import iterate_over_all_documents_in_collection, retrieve_tagged_documents_from_database
from kgextractiontoolbox.document.document import TaggedDocument, DocumentSection, TaggedEntity
from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgtests.util import tmp_rel_path


def create_copy(t_doc, clear_tag=False, clear_sections=False, clear_classifications=False):
    t_doc_copy = copy.deepcopy(t_doc)

    if clear_tag:
        t_doc_copy.tags.clear()
    if clear_sections:
        t_doc_copy.sections.clear()
    if clear_classifications:
        t_doc_copy.classification.clear()

    return t_doc_copy


def prepare_test_doc():
    test_retrieve_doc = TaggedDocument(id=1, title="A", abstract="This is a test")
    test_retrieve_doc.sections.append(DocumentSection(position=0, title="Introduction", text="Simvastatin is cool."))
    test_retrieve_doc.sections.append(DocumentSection(position=1, title="Introduction", text="Simvastatin is sometimes cool."))
    test_retrieve_doc.sections.append(DocumentSection(position=5, title="Results", text="Simvastatin is lovely."))
    test_retrieve_doc.tags.append(TaggedEntity(document=1, ent_id="this", ent_type="A", start=2, end=6, text="this"))
    test_retrieve_doc.tags.append(TaggedEntity(document=1, ent_id="test", ent_type="A", start=12, end=16, text="test"))
    test_retrieve_doc.tags.append(TaggedEntity(document=1, ent_id="Simvastatin", ent_type="A", start=30, end=41, text="Simvastatin"))
    test_retrieve_doc.tags.append(TaggedEntity(document=1, ent_id="cool", ent_type="A", start=45, end=49, text="cool"))
    test_retrieve_doc.classification.update({"PlantSpecific": "Antioxida*:Antioxidant(63, 74) AND plant:plant(243, 248);Extract:extract(1826, 1833);Extracts:extracts(249, 257)"})
    test_retrieve_doc.classification.update({"Pharmaceutical": "antimicrob*:Antimicrobial(48, 61);antioxidan*:Antioxidant(63, 74);cytotoxi*:Cytotoxic(80, 89);inhibitor*:inhibitory(978, 988);nanoparticle*:Nanoparticles(21, 34);toxi*:toxic(84, 89);vitamin*:vitamin(1653, 1660);anti*:Antimicrobial(48, 61) AND agent*:Agents(90, 96)"})

    test_retrieve_doc2 = TaggedDocument(id=2, title="B", abstract="This is another test")
    test_retrieve_doc2.sections.append(DocumentSection(position=0, title="Introduction", text="Simvastatin is nice."))
    test_retrieve_doc2.sections.append(DocumentSection(position=1, title="Introduction", text="Simvastatin is sometimes nice."))
    test_retrieve_doc2.sections.append(DocumentSection(position=5, title="Results", text="Simvastatin is lovely."))
    test_retrieve_doc2.tags.append(TaggedEntity(document=2, ent_id="this", ent_type="A", start=2, end=6, text="this"))
    test_retrieve_doc2.tags.append(TaggedEntity(document=2, ent_id="test", ent_type="A", start=18, end=22, text="test"))
    test_retrieve_doc2.tags.append(TaggedEntity(document=2, ent_id="Simvastatin", ent_type="A", start=30, end=41, text="Simvastatin"))
    test_retrieve_doc2.tags.append(TaggedEntity(document=2, ent_id="nice", ent_type="A", start=45, end=49, text="nice"))
    test_retrieve_doc2.classification.update({"PlantSpecific2": "Antioxida*:Antioxidant(63, 74) AND plant:plant(243, 248);Extract:extract(1826, 1833);Extracts:extracts(249, 257)"})
    test_retrieve_doc2.classification.update({"Pharmaceutical2": "antimicrob*:Antimicrobial(48, 61);antioxidan*:Antioxidant(63, 74);cytotoxi*:Cytotoxic(80, 89);inhibitor*:inhibitory(978, 988);nanoparticle*:Nanoparticles(21, 34);toxi*:toxic(84, 89);vitamin*:vitamin(1653, 1660);anti*:Antimicrobial(48, 61) AND agent*:Agents(90, 96)"})

    test_retrieve_doc_path = tmp_rel_path("retrieve_testdoc.json")
    with open(test_retrieve_doc_path, 'w') as f:
        json.dump(test_retrieve_doc.to_dict(), f)
    test_retrieve_doc_path2 = tmp_rel_path("retrieve_testdoc2.json")
    with open(test_retrieve_doc_path2, 'w') as g:
        json.dump(test_retrieve_doc2.to_dict(), g)

    document_bulk_load(test_retrieve_doc_path, "TestRetrieve", ignore_tags=False)
    document_bulk_load(test_retrieve_doc_path2, "TestRetrieve", ignore_tags=False)

    return test_retrieve_doc, test_retrieve_doc2


class TestRetrieve(unittest.TestCase):
    def test_none(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        test_none_doc = create_copy(test_retrieve_doc, clear_tag=True, clear_sections=True, clear_classifications=True)
        test_none_doc2 = create_copy(test_retrieve_doc2, clear_tag=True, clear_sections=True, clear_classifications=True)

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve"))

        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_none_doc, retrieve_docs[0])
        self.assertEqual(test_none_doc2, retrieve_docs[1])
        self.assertNotEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertNotEqual(test_retrieve_doc2, retrieve_docs[1])

    def test_all(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve", consider_tag=True, consider_sections=True, consider_classification=True))
        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertEqual(test_retrieve_doc2, retrieve_docs[1])

    def test_tag(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        test_tag_doc = create_copy(test_retrieve_doc, clear_sections=True, clear_classifications=True)
        test_tag_doc2 = create_copy(test_retrieve_doc2, clear_sections=True, clear_classifications=True)

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve", consider_tag=True))

        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_tag_doc, retrieve_docs[0])
        self.assertEqual(test_tag_doc2, retrieve_docs[1])
        self.assertNotEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertNotEqual(test_retrieve_doc2, retrieve_docs[1])

    def test_sections(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        test_sections_doc = create_copy(test_retrieve_doc, clear_tag=True, clear_classifications=True)
        test_sections_doc2 = create_copy(test_retrieve_doc2, clear_tag=True, clear_classifications=True)

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve", [1, 2], consider_sections=True))

        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_sections_doc, retrieve_docs[0])
        self.assertEqual(test_sections_doc2, retrieve_docs[1])
        self.assertNotEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertNotEqual(test_retrieve_doc2, retrieve_docs[1])

    def test_classification(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        test_classifications_doc = create_copy(test_retrieve_doc, clear_tag=True, clear_sections=True)
        test_classifications_doc2 = create_copy(test_retrieve_doc2, clear_tag=True, clear_sections=True)

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve", [1, 2], consider_classification=True))

        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_classifications_doc, retrieve_docs[0])
        self.assertEqual(test_classifications_doc2, retrieve_docs[1])
        self.assertNotEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertNotEqual(test_retrieve_doc2, retrieve_docs[1])

    def test_tags_with_sections(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        test_tag_sec_doc = create_copy(test_retrieve_doc, clear_classifications=True)
        test_tag_sec_doc2 = create_copy(test_retrieve_doc2, clear_classifications=True)

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve", [1, 2], consider_tag=True, consider_sections=True))
        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_tag_sec_doc, retrieve_docs[0])
        self.assertEqual(test_tag_sec_doc2, retrieve_docs[1])
        self.assertNotEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertNotEqual(test_retrieve_doc2, retrieve_docs[1])

    def test_tags_with_classifications(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        test_tag_class_doc = create_copy(test_retrieve_doc, clear_sections=True)
        test_tag_class_doc2 = create_copy(test_retrieve_doc2, clear_sections=True)

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve", consider_tag=True, consider_classification=True))

        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_tag_class_doc, retrieve_docs[0])
        self.assertEqual(test_tag_class_doc2, retrieve_docs[1])
        self.assertNotEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertNotEqual(test_retrieve_doc2, retrieve_docs[1])

    def test_sections_with_classifications(self):
        test_retrieve_doc, test_retrieve_doc2 = prepare_test_doc()

        test_sec_class_doc = create_copy(test_retrieve_doc, clear_tag=True)
        test_sec_class_doc2 = create_copy(test_retrieve_doc2, clear_tag=True)

        session = Session.get()
        retrieve_docs = list(iterate_over_all_documents_in_collection(session, "TestRetrieve", consider_sections=True, consider_classification=True))

        self.assertEqual(2, len(retrieve_docs))
        self.assertEqual(test_sec_class_doc, retrieve_docs[0])
        self.assertEqual(test_sec_class_doc2, retrieve_docs[1])
        self.assertNotEqual(test_retrieve_doc, retrieve_docs[0])
        self.assertNotEqual(test_retrieve_doc2, retrieve_docs[1])
