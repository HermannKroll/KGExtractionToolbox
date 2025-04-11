import unittest

from kgextractiontoolbox.util.helpers import chunks


class TestProgress(unittest.TestCase):

    def test_chunk(self):
        numbers = [i for i in range(10000)]

        idx = 0
        for chunk in chunks(numbers, n=10):
            for element in chunk:
                self.assertEqual(element, idx)
                idx += 1

        self.assertEqual(idx, 10000)

    def test_chunk_large(self):
        numbers = [i for i in range(100000)]

        idx = 0
        for chunk in chunks(numbers, n=10):
            for element in chunk:
                self.assertEqual(element, idx)
                idx += 1

        self.assertEqual(idx, 100000)