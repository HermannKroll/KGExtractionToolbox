import json
from unittest import TestCase

from spacy.lang.en import English

from kgextractiontoolbox.document.document import TaggedDocument, DocumentSection, TaggedEntity
from kgextractiontoolbox.extraction.extraction_utils import filter_document_sentences_without_tags
from kgtests.util import get_test_resource_filepath, tmp_rel_path


class ExtractionUtilsTestCase(TestCase):

    def test_filter_sentences_by_remaining_sentences(self):
        nlp = English()  # just the language with no model
        nlp.add_pipe("sentencizer")

        test26 = get_test_resource_filepath("PubMed26.txt")
        doc_id = 26

        doc2sentences, doc2tags = filter_document_sentences_without_tags(1, test26, nlp)
        self.assertEqual(1, len(doc2sentences))
        self.assertEqual(2, len(doc2sentences[doc_id]))

        self.assertEqual(
            'A double-blind study with intra-individual comparisons was carried out to investigate the effects of 15 mg of (8r)-3alpha-hydroxy-8-isopropyl-1alphaH-tropanium bromide(+/-)-tropate (Sch 1000), 15 mg Sch 1000 + 10 mg oxazepam, 10 mg oxazepam and placebo with oral administration in randomized sequence on gastric juice volume, amount of acid, concentration and pH values in 12 healthy volunteers. ',
            doc2sentences[doc_id][0])
        self.assertEqual('Stimulation was effected by 1 mug/kg/h pentagastrin via drip infusion. ',
                         doc2sentences[doc_id][1])

        self.assertEqual(1, len(doc2tags))
        self.assertEqual(5, len(doc2tags[doc_id]))

        test54 = get_test_resource_filepath("PubMed54.txt")
        doc_id = 54

        doc2sentences, doc2tags = filter_document_sentences_without_tags(1, test54, nlp)
        self.assertEqual(1, len(doc2sentences))
        self.assertEqual(1, len(doc2sentences[doc_id]))

        self.assertEqual(
            'The hydrolytic action of the basic enzyme was found to consist of two sequential events: (a) hydrolysis of 70% of the total cell ph osphatidylcholine without any evident hemolysis; and (b) complete hydrolysis of the remaining phosphatidylcholine, followed closely by extensive phosphatidylethanolamine hydrolysis and finally with onset of hemolysis, attack on the phosphatidylserine. ',
            doc2sentences[doc_id][0])

        self.assertEqual(1, len(doc2tags))
        self.assertEqual(2, len(doc2tags[doc_id]))

        test_collection = get_test_resource_filepath("PubTatorCollection.txt")
        doc2sentences, doc2tags = filter_document_sentences_without_tags(2, test_collection, nlp)
        self.assertEqual(2, len(doc2sentences))
        self.assertEqual(2, len(doc2tags))

        self.assertEqual(3, len(doc2sentences[1313813]))
        self.assertEqual(
            'Protein synthesis and secretion were assayed by following the incorporation or release, respectively, of [35S]methionine-labeled TCA-precipitable protein. ',
            doc2sentences[1313813][0])
        self.assertEqual(
            'The extent of protein secretion was unaffected by the phorbol ester PMA, 8-bromo-cAMP, or 8- bromo-cGMP but was doubled by the Ca2+ ionophore ionomycin. ',
            doc2sentences[1313813][1])
        self.assertEqual(
            'In a pulse- label protocol in which proteins were prelabeled for 1 h before a chase period, constitutive secretion was unaffected by depletion of cytosolic Ca2+ but ionomycin was found to give a twofold stimulation of the secretion of presynthesized protein in a Ca(2+)-dependent manner. ',
            doc2sentences[1313813][2])

        self.assertEqual(3, len(doc2sentences[1313814]))
        self.assertEqual(
            'Nerve growth factor nonresponsive pheochromocytoma cells: altered internalization results in signaling dysfunction. ',
            doc2sentences[1313814][0])
        self.assertEqual(
            'Variant rat pheochromocytoma (PC12) cells which fail to respond to nerve growth factor (NGF) (PC12nnr5) (Green, S. H., R. E. Rydel, J. L. Connoly, and L. A. Greene. ',
            doc2sentences[1313814][1])
        self.assertEqual(
            'They are apparently composed of two membrane-bound proteins, p75 and the protooncogene trk, both of which bind NGF, and apparently contribute singularly or in concert to the two observed affinities, and to the promotion of the NGF effects. ',
            doc2sentences[1313814][2])

        self.assertEqual(10, len(doc2tags[1313813]))
        self.assertEqual(10, len(doc2tags[1313814]))

    def test_filter_sentences_by_remaining_new_tag_positions(self):
        nlp = English()  # just the language with no model
        nlp.add_pipe("sentencizer")

        test26 = get_test_resource_filepath("PubMed26.txt")
        doc_id = 26

        doc2sentences, doc2tags = filter_document_sentences_without_tags(1, test26, nlp)
        new_text = ''.join(doc2sentences[doc_id])
        for tag in doc2tags[doc_id]:
            t_id, t_text, t_start, t_end = tag.ent_id, tag.text, tag.start, tag.end
            self.assertEqual(t_text, new_text[t_start:t_end])

        test54 = get_test_resource_filepath("PubMed54.txt")
        doc_id = 54
        doc2sentences, doc2tags = filter_document_sentences_without_tags(1, test54, nlp)
        new_text = ''.join(doc2sentences[doc_id])
        for tag in doc2tags[doc_id]:
            t_id, t_text, t_start, t_end = tag.ent_id, tag.text, tag.start, tag.end
            self.assertEqual(t_text, new_text[t_start:t_end])

        test_collection = get_test_resource_filepath("PubTatorCollection.txt")
        doc2sentences, doc2tags = filter_document_sentences_without_tags(2, test_collection, nlp)
        for doc_id in [1313813, 1313814]:
            new_text = ''.join(doc2sentences[doc_id])
            for tag in doc2tags[doc_id]:
                t_id, t_text, t_start, t_end = tag.ent_id, tag.text, tag.start, tag.end
                self.assertEqual(t_text, new_text[t_start:t_end])

    def test_filter_sentences_in_sections_by_remaining_sentences(self):
        nlp = English()  # just the language with no model
        nlp.add_pipe("sentencizer")

        test_doc1 = TaggedDocument(id=1, title="A", abstract="This is a test")
        test_doc1.sections.append(DocumentSection(position=0, title="Introduction", text="Simvastatin is cool."))
        test_doc1.tags.append(TaggedEntity(document=1, ent_id="this", ent_type="A", start=2, end=6, text="this"))
        test_doc1.tags.append(TaggedEntity(document=1, ent_id="test", ent_type="A", start=12, end=16, text="test"))
        test_doc1.tags.append(TaggedEntity(document=1, ent_id="this", ent_type="A", start=2, end=6, text="this"))
        test_doc1.tags.append(
            TaggedEntity(document=1, ent_id="Simvastatin", ent_type="A", start=30, end=41, text="Simvastatin"))
        test_doc1.tags.append(TaggedEntity(document=1, ent_id="cool", ent_type="A", start=45, end=49, text="cool"))

        test_doc1_path = tmp_rel_path("extraction_testdoc1.json")
        with open(test_doc1_path, 'w') as f:
            json.dump(test_doc1.to_dict(), f)

        doc2sentences, doc2tags = filter_document_sentences_without_tags(1, test_doc1_path, nlp, consider_sections=False)
        self.assertEqual(1, len(doc2sentences))
        self.assertEqual(1, len(doc2sentences[1]))
        self.assertEqual('This is a test. ', doc2sentences[1][0])

        doc2sentences, doc2tags = filter_document_sentences_without_tags(1, test_doc1_path, nlp, consider_sections=True)
        self.assertEqual(1, len(doc2sentences))
        self.assertEqual(2, len(doc2sentences[1]))
        self.assertEqual('This is a test. ', doc2sentences[1][0])
        self.assertEqual('Simvastatin is cool. ', doc2sentences[1][1])
