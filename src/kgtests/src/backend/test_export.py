import unittest

from kgextractiontoolbox.document.export import export
from kgextractiontoolbox.document.load_document import document_bulk_load, insert_taggers
from kgextractiontoolbox.backend.database import Session
from kgtests import util


def setup_module(module):
    test_mapping = {"Drug": ("Drugtagger", "1.0"), "Disease": ("Diseasetagger", "1.0")}
    insert_taggers(*[(name, version) for name, version in test_mapping.values()])
    document_bulk_load(util.get_test_resource_filepath("infiles/test_export/in/"), "TEST_EXPORT", test_mapping,
                       ignore_tags=False)
    session = Session.get()
    pass


def teardown_module(module):
    util.clear_database()


class TestExport(unittest.TestCase):
    def test_export_pubtator(self):
        outfile = util.tmp_rel_path("export_out")
        testfile = util.get_test_resource_filepath("infiles/test_export/out/pubtator.txt")
        export(outfile, export_tags=True, content=True, export_format="pubtator", collection="TEST_EXPORT")
        with open(outfile) as of, open(testfile) as tf:
            self.assertEqual(tf.read(), of.read())

    def test_export_json(self):
        outfile = util.tmp_rel_path("export_out")
        testfile = util.get_test_resource_filepath("infiles/test_export/out/json.txt")

        export(outfile, export_tags=True, export_format="json", collection="TEST_EXPORT")
        with open(outfile) as of, open(testfile) as tf:
            self.assertEqual(tf.read(), of.read())

    def test_export_json_line(self):
        outfile = util.tmp_rel_path("export_out")
        testfile = util.get_test_resource_filepath("infiles/test_export/out/jsonl.txt")

        export(outfile, export_tags=True, export_format="jsonl", collection="TEST_EXPORT")
        with open(outfile) as of, open(testfile) as tf:
            self.assertEqual(tf.read().replace(' ', ''), of.read().replace(' ', ''))

    def test_export_classification(self):
        outfile_classification = util.tmp_rel_path("export_out")
        testfile_classification = util.get_test_resource_filepath("infiles/test_export/out/classification.txt")

        export(outfile_classification, export_tags=True, export_format="json", export_classification=True, collection="TEST_EXPORT")
        with open(outfile_classification) as of, open(testfile_classification) as tf:
            self.assertEqual(tf.read(), of.read())

        outfile_no_classification = util.tmp_rel_path("export_out")
        testfile_no_classification = util.get_test_resource_filepath("infiles/test_export/out/no_classification.txt")

        export(outfile_no_classification, export_tags=True, export_format="json", collection="TEST_EXPORT")
        with open(outfile_no_classification) as of, open(testfile_no_classification) as tf:
            self.assertEqual(tf.read(), of.read())
