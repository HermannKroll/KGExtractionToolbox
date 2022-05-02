from unittest import TestCase

from kgextractiontoolbox.extraction.analyze_openie_tuples import check_is_complex


class OpenIEAnalysisTest(TestCase):

    def test_check_is_complex(self):
        self.assertTrue(check_is_complex("This is and that"))
        self.assertTrue(check_is_complex("This is a complex sentence because it contains multiple phrases"))
        self.assertTrue(check_is_complex("Think about the following conditions: a and b"))
        self.assertTrue(check_is_complex("A and b"))
        self.assertTrue(check_is_complex("A or b"))
        self.assertTrue(check_is_complex("A OR b"))
        self.assertTrue(check_is_complex("A, B, C"))
        self.assertTrue(check_is_complex("A? B"))
        self.assertTrue(check_is_complex("However, we see that this is a problem"))
        self.assertTrue(check_is_complex("We believe that humans are"))
        self.assertTrue(check_is_complex("However, this is complex"))
        self.assertTrue(check_is_complex("Thus a is good"))
        self.assertTrue(check_is_complex("Hence a is good"))

    def test_check_is_not_complex(self):
        self.assertFalse(check_is_complex("We think about simple sentences."))
        self.assertFalse(check_is_complex("We think about simple sentences"))
        self.assertFalse(check_is_complex("He played football yesterday"))
        self.assertFalse(check_is_complex("a is great"))
        self.assertFalse(check_is_complex("a is great."))
        self.assertFalse(check_is_complex("a is great.?.."))
        self.assertFalse(check_is_complex("a is great...."))
        self.assertFalse(check_is_complex("Thisdue isbecause a test"))
        self.assertFalse(check_is_complex("This is a testor"))
        self.assertFalse(check_is_complex("This is a testand"))
        self.assertFalse(check_is_complex(""))
        self.assertFalse(check_is_complex("..."))
