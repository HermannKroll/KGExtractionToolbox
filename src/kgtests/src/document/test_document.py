import json
import unittest

from spacy.lang.en import English

from kgextractiontoolbox.document.document import TaggedEntity, TaggedDocument, parse_tag_list, DocumentSection
from kgextractiontoolbox.document.extract import read_tagged_documents
from kgtests.util import get_test_resource_filepath, tmp_rel_path


class TestDocument(unittest.TestCase):

    def setUp(self) -> None:
        nlp = English()  # just the language with no model
        nlp.add_pipe("sentencizer")
        self.nlp = nlp

    def test_parse_tag_list(self):
        tags = parse_tag_list(get_test_resource_filepath("infiles/onlytags.txt"))
        self.assertIsNotNone(tags)
        strings = [repr(tag) for tag in tags]
        self.assertIn("<Entity 0,8,prote ins,DosageForm,Desc1>", strings)
        self.assertIn("<Entity 1103,1112,proteins,DosageForm,Desc1>", strings)

    def test_Tagged_Document_from_putatorfile(self):
        in_file = get_test_resource_filepath("infiles/test_metadictagger/abbrev_tagged.txt")
        tagged_doc = [d for d in read_tagged_documents(in_file)][0]
        self.assertIn(TaggedEntity(None, 32926486, 97, 111, "ethylene oxide", "Excipient", "Ethylene oxide"),
                      tagged_doc.tags)
        self.assertIn(TaggedEntity(None, 32926486, 97, 111, "Ethylene Oxide", "Chemical", "MESH:D005027"),
                      tagged_doc.tags)
        self.assertIn(TaggedEntity(None, 32926486, 97, 105, "ethylene", "Excipient", "Ethylene"),
                      tagged_doc.tags)
        tagged_doc.clean_tags()
        self.assertIn(TaggedEntity(None, 32926486, 97, 111, "ethylene oxide", "Excipient", "Ethylene oxide"),
                      tagged_doc.tags)
        self.assertIn(TaggedEntity(None, 32926486, 97, 111, "Ethylene Oxide", "Chemical", "MESH:D005027"),
                      tagged_doc.tags)
        self.assertNotIn(TaggedEntity(None, 32926486, 97, 105, "ethylene", "Excipient", "Ethylene"),
                         tagged_doc.tags)

    def test_Tagged_Document_read_write_pubtator(self):
        in_file = get_test_resource_filepath("infiles/test_metadictagger/abbrev_tagged.txt")
        out_file = tmp_rel_path("tagdoc_out.txt")
        tagged_doc = TaggedDocument(in_file)
        with open(out_file, "w+") as of:
            of.write(str(tagged_doc))
        with open(in_file) as inf, open(out_file) as of:
            self.assertEqual(inf.read(), of.read())

    def test_Tagged_Document_read_write_json(self):
        in_file = get_test_resource_filepath("infiles/test_metadictagger/abbrev_tagged.json")
        out_file = tmp_rel_path("tagdoc_out.txt")
        tagged_doc = TaggedDocument(in_file)
        with open(out_file, "w+") as of:
            json.dump(tagged_doc.to_dict(), of)
            print(json.dumps(tagged_doc.to_dict()))
        with open(in_file) as inf, open(out_file) as of:
            self.assertEqual(inf.read(), of.read())

    def test_load_tagged_pubtator_doc(self):
        content = ""
        with open(get_test_resource_filepath('PMC1313813.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content)

        self.assertEqual(1313813, doc.id)
        self.assertEqual('Proteins are secreted by both constitutive and regulated secretory pathways in '
                         'lactating mouse mammary epithelial cells',
                         doc.title.strip())
        self.assertEqual(19, len(doc.tags))

    def test_load_untagged_pubtator_doc(self):
        content = ""
        with open(get_test_resource_filepath('PMC1313813Untagged.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content)

        self.assertEqual(1313813, doc.id)
        self.assertEqual('Proteins are secreted by both constitutive and regulated secretory pathways in '
                         'lactating mouse mammary epithelial cells',
                         doc.title.strip())
        self.assertEqual(0, len(doc.tags))

    def test_split_sentences(self):
        content = ""
        with open(get_test_resource_filepath('PubMed26.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(13, len(doc.sentence_by_id))
        self.assertEqual(
            "SStudies on the action of an anticholinergic agent in combination with a tranquilizer on gastric juice secretion in mann.",
            doc.sentence_by_id[0].text)
        self.assertEqual(0, doc.sentence_by_id[0].start)
        self.assertEqual(121, doc.sentence_by_id[0].end)

        self.assertEqual(
            "As compared with placebo, it was not possible to establish an effect on secretion volume for oxazepam alone.",
            doc.sentence_by_id[7].text)
        self.assertEqual(1040, doc.sentence_by_id[7].start)
        self.assertEqual(1148, doc.sentence_by_id[7].end)

        self.assertEqual("The results are discussed.",
                         doc.sentence_by_id[12].text)

        content = ""
        with open(get_test_resource_filepath('PubMed54.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(16, len(doc.sentence_by_id))
        self.assertEqual("Phospholipase A2 as a probe of phospholipid distribution in erythrocyte membranes.",
                         doc.sentence_by_id[0].text)

        self.assertEqual("At pH 7.4 and 10 mM Ca2+ only stage (a) occurred.",
                         doc.sentence_by_id[5].text)

        self.assertEqual("Certain facets of this problem are discussed.",
                         doc.sentence_by_id[15].text)

    def test_split_sentences2(self):
        text = "This is a text about the cyp3.a4 enzyme. Lets see whether splitting works."
        doc_nlp = self.nlp(text)
        sentences = list([str(s) for s in doc_nlp.sents])
        self.assertEqual("This is a text about the cyp3.a4 enzyme.", sentences[0])
        self.assertEqual("Lets see whether splitting works.", sentences[1])

    def test_find_correct_tags(self):
        content = ""
        with open(get_test_resource_filepath('PubMed26.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(4, len(doc.entities_by_ent_id))
        self.assertEqual(2, len(doc.entities_by_ent_id['MESH:D000284']))
        self.assertEqual(1, len(doc.entities_by_ent_id['MESH:D007262']))
        self.assertEqual(7, len(doc.entities_by_ent_id['DB00842']))
        self.assertEqual(1, len(doc.entities_by_ent_id['DB00183']))

        content = ""
        with open(get_test_resource_filepath('PubMed54.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(4, len(doc.entities_by_ent_id))
        self.assertEqual(1, len(doc.entities_by_ent_id['DB04327']))
        self.assertEqual(1, len(doc.entities_by_ent_id['DB00144']))
        self.assertEqual(1, len(doc.entities_by_ent_id['DB09341']))
        self.assertEqual(2, len(doc.entities_by_ent_id['DB11133']))

    def test_find_correct_tags_in_sentences(self):
        content = ""
        with open(get_test_resource_filepath('PubMed26.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(4, len(doc.sentences_by_ent_id))
        self.assertSetEqual({1}, doc.sentences_by_ent_id['MESH:D000284'])
        self.assertSetEqual({4}, doc.sentences_by_ent_id['MESH:D007262'])
        self.assertSetEqual({1, 6, 7, 8, 11}, doc.sentences_by_ent_id['DB00842'])
        self.assertSetEqual({4}, doc.sentences_by_ent_id['DB00183'])

        content = ""
        with open(get_test_resource_filepath('PubMed54.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(4, len(doc.sentences_by_ent_id))
        self.assertSetEqual({4}, doc.sentences_by_ent_id['DB04327'])
        self.assertSetEqual({4}, doc.sentences_by_ent_id['DB00144'])
        self.assertSetEqual({7}, doc.sentences_by_ent_id['DB09341'])
        self.assertSetEqual({0, 3}, doc.sentences_by_ent_id['DB11133'])

    def test_sentence_to_ent_id_mapping(self):
        content = ""
        with open(get_test_resource_filepath('PubMed26.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(6, len(doc.entities_by_sentence))

        self.assertEqual({'MESH:D000284', 'DB00842'}, {t.ent_id for t in doc.entities_by_sentence[1]})
        self.assertEqual({'MESH:D007262', 'DB00183'}, {t.ent_id for t in doc.entities_by_sentence[4]})
        self.assertEqual({'DB00842'}, {t.ent_id for t in doc.entities_by_sentence[6]})
        self.assertEqual({'DB00842'}, {t.ent_id for t in doc.entities_by_sentence[7]})
        self.assertEqual({'DB00842'}, {t.ent_id for t in doc.entities_by_sentence[8]})
        self.assertEqual({'DB00842'}, {t.ent_id for t in doc.entities_by_sentence[11]})

        content = ""
        with open(get_test_resource_filepath('PubMed54.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content, spacy_nlp=self.nlp)

        self.assertEqual(4, len(doc.sentences_by_ent_id))

        self.assertEqual({'DB04327', 'DB00144'}, {t.ent_id for t in doc.entities_by_sentence[4]})
        self.assertEqual({'DB09341'}, {t.ent_id for t in doc.entities_by_sentence[7]})
        self.assertEqual({'DB11133'}, {t.ent_id for t in doc.entities_by_sentence[0]})
        self.assertEqual({'DB11133'}, {t.ent_id for t in doc.entities_by_sentence[3]})

    def test_composite_tag_mention(self):
        # There are composite entity mentions like
        # 24729111	19	33	myxoedema coma	Disease	D007037|D003128	myxoedema|coma
        with open(get_test_resource_filepath('pubtator_composite_tags.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content)

        self.assertIn('D007037', {t.ent_id for t in doc.tags})
        self.assertIn('D003128', {t.ent_id for t in doc.tags})
        self.assertIn('D000638', {t.ent_id for t in doc.tags})
        self.assertIn('D007037', {t.ent_id for t in doc.tags})
        self.assertIn('D007035', {t.ent_id for t in doc.tags})

        self.assertIn(TaggedEntity(None, 24729111, 19, 28, "myxoedema", "Disease", "D007037"),
                      doc.tags)
        self.assertIn(TaggedEntity(None, 24729111, 29, 33, "coma", "Disease", "D003128"),
                      doc.tags)

        self.assertIn(TaggedEntity(None, 24729111, 963, 972, "myxoedema", "Disease", "D007037"),
                      doc.tags)
        self.assertIn(TaggedEntity(None, 24729111, 973, 977, "coma", "Disease", "D003128"),
                      doc.tags)

    def test_empty_ent_id_in_tag(self):
        with open(get_test_resource_filepath('pubtator_empty_id.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content)
        # empty ids should be ignored
        self.assertNotIn(TaggedEntity(None, 24729111, 0, 10, "Amiodarone", "Chemical", ""), doc.tags)

    def test_only_tags_document(self):
        # There are composite entity mentions like
        # 24729111	19	33	myxoedema coma	Disease	D007037|D003128	myxoedema|coma
        with open(get_test_resource_filepath('pubtator_only_tags.txt'), 'rt') as f:
            content = f.read()
        doc = TaggedDocument(content)

        self.assertIsNone(doc.title)
        self.assertIsNone(doc.abstract)
        self.assertEqual(24729111, doc.id)
        self.assertIn('D007037', {t.ent_id for t in doc.tags})
        self.assertIn('D003128', {t.ent_id for t in doc.tags})
        self.assertIn('D000638', {t.ent_id for t in doc.tags})
        self.assertIn('D007037', {t.ent_id for t in doc.tags})
        self.assertIn('D007035', {t.ent_id for t in doc.tags})

        self.assertIn(TaggedEntity(None, 24729111, 19, 28, "myxoedema", "Disease", "D007037"),
                      doc.tags)
        self.assertIn(TaggedEntity(None, 24729111, 29, 33, "coma", "Disease", "D003128"),
                      doc.tags)

        self.assertIn(TaggedEntity(None, 24729111, 963, 972, "myxoedema", "Disease", "D007037"),
                      doc.tags)
        self.assertIn(TaggedEntity(None, 24729111, 973, 977, "coma", "Disease", "D003128"),
                      doc.tags)

    def test_parse_pubtator_documents(self):
        count = 0
        for doc in read_tagged_documents(get_test_resource_filepath("pubmed_sample.pubtator")):
            self.assertEqual(True, doc.has_content())
            count += 1
        self.assertEqual(10, count)

    def test_get_text_content(self):
        text = "Simvastatin (ST) is a drug. Simvastatin is cool. Cool is also simVAStatin. ST is simvastatine."

        doc1 = TaggedDocument(title="", abstract="", id=1)
        doc1.sections.append(DocumentSection(position=0, title="", text=""))
        doc1.sections.append(DocumentSection(position=0, title="", text=""))
        doc1.sections.append(DocumentSection(position=0, title="", text=text))

        self.assertEqual("", doc1.get_text_content().strip())

        self.assertEqual(text, doc1.get_text_content(sections=True).strip())
        self.assertEqual(7 * ' ' + text, doc1.get_text_content(sections=True))

        doc2 = TaggedDocument(title="Hello", abstract="Test", id=1)
        doc2.sections.append(DocumentSection(position=0, title="Introduction", text="Hello"))
        doc2.sections.append(DocumentSection(position=0, title="Test", text=""))
        self.assertEqual("Hello Test", doc2.get_text_content())
        self.assertEqual("Hello Test Introduction Hello Test ", doc2.get_text_content(sections=True))

    def test_split_sentences_sections(self):
        doc1 = TaggedDocument(title="This is a text about the cyp3.a4 enzyme.", abstract="Blank.", id=1)
        doc1.sections.append(
            DocumentSection(position=0, title="Introduction", text="Lets see whether splitting works."))
        doc1.sections.append(DocumentSection(position=0, title="Background", text="Lets hope that splitting works."))

        # sections should be ignored
        doc1._compute_nlp_indexes(self.nlp, sections=False)
        self.assertEqual(2, len(doc1.sentence_by_id))
        self.assertEqual(0, doc1.sentence_by_id[0].start)
        self.assertEqual(40, doc1.sentence_by_id[0].end)

        # now consider sections
        doc1._compute_nlp_indexes(self.nlp, sections=True)
        self.assertEqual(6, len(doc1.sentence_by_id))
        self.assertEqual("This is a text about the cyp3.a4 enzyme.", doc1.sentence_by_id[0].text)
        self.assertEqual(0, doc1.sentence_by_id[0].start)
        self.assertEqual(40, doc1.sentence_by_id[0].end)

        self.assertEqual("Blank.", doc1.sentence_by_id[1].text)
        self.assertEqual(41, doc1.sentence_by_id[1].start)
        self.assertEqual(47, doc1.sentence_by_id[1].end)

        self.assertEqual("Introduction", doc1.sentence_by_id[2].text)
        self.assertEqual(48, doc1.sentence_by_id[2].start)
        self.assertEqual(60, doc1.sentence_by_id[2].end)

        self.assertEqual("Lets see whether splitting works.", doc1.sentence_by_id[3].text)
        self.assertEqual(61, doc1.sentence_by_id[3].start)
        self.assertEqual(94, doc1.sentence_by_id[3].end)

        self.assertEqual("Background", doc1.sentence_by_id[4].text)
        self.assertEqual(95, doc1.sentence_by_id[4].start)
        self.assertEqual(105, doc1.sentence_by_id[4].end)

        self.assertEqual("Lets hope that splitting works.", doc1.sentence_by_id[5].text)
        self.assertEqual(106, doc1.sentence_by_id[5].start)
        self.assertEqual(137, doc1.sentence_by_id[5].end)

    def test_clean_tags_not_valid(self):
        doc1 = TaggedDocument()
        doc1.tags.append(TaggedEntity(document=1, start=0, end=10, text="simvastatin", ent_id="D1", ent_type="Drug"))
        doc1.tags.append(TaggedEntity(document=1, start=0, end=10, text="simvastatin", ent_id=None, ent_type=None))

        self.assertEqual(2, len(doc1.tags))
        doc1.clean_tags()
        # Second tag is not valid
        self.assertEqual(1, len(doc1.tags))

    def test_clean_tags_longer_mention(self):
        doc1 = TaggedDocument()
        doc1.tags.append(TaggedEntity(document=1, start=0, end=10, text="simvastatin", ent_id="D1", ent_type="Drug"))
        doc1.tags.append(
            TaggedEntity(document=1, start=0, end=15, text="simvastatin acid", ent_id="D1", ent_type="Drug"))
        self.assertEqual(2, len(doc1.tags))
        # Test: Small simvastatin mention should be removed
        doc1.clean_tags()
        self.assertEqual(1, len(doc1.tags))

    def test_clean_tags_duplicated(self):
        doc1 = TaggedDocument()
        doc1.tags.append(TaggedEntity(document=1, start=0, end=10, text="simvastatin", ent_id="D1", ent_type="Drug"))
        doc1.tags.append(TaggedEntity(document=1, start=0, end=10, text="simvastatin", ent_id="D1", ent_type="Drug"))
        self.assertEqual(2, len(doc1.tags))
        doc1.clean_tags()
        # Duplicated tag should be removed
        self.assertEqual(1, len(doc1.tags))


    def test_tagged_document_fulltext(self):
        doc1 = TaggedDocument(id=1, title="title", abstract="abstract")
        self.assertEqual("1|t|title\n1|a|abstract\n\n", str(doc1))
        self.assertEqual("title abstract", doc1.get_text_content())

        doc1.sections.append(DocumentSection(0, "section 1", "hallo"))

        self.assertEqual("1|t|title\n1|a|abstract section 1 hallo\n\n", str(doc1))
        self.assertEqual("title abstract", doc1.get_text_content())
        self.assertEqual("title abstract section 1 hallo", doc1.get_text_content(sections=True))

        doc1.sections.append(DocumentSection(2, "section 2", "das ist ein test"))

        self.assertEqual("1|t|title\n1|a|abstract section 1 hallo section 2 das ist ein test\n\n", str(doc1))
        self.assertEqual("title abstract", doc1.get_text_content())
        self.assertEqual("title abstract section 1 hallo section 2 das ist ein test", doc1.get_text_content(sections=True))