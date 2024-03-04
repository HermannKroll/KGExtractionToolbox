import unittest

from kgextractiontoolbox.document.export import export
from kgextractiontoolbox.document.load_document import document_bulk_load
from kgextractiontoolbox.backend.database import Session
from kgtests import util


def setup_module(module):
    test_mapping = {"Drug": ("Drugtagger", "1.0"), "Disease": ("Diseasetagger", "1.0")}
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
