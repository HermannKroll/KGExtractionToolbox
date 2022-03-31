import json
import os
import unittest

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.config import BACKEND_CONFIG
from kgextractiontoolbox.backend.models import Tagger
from kgtests.util import tmp_rel_path


class TestSession(unittest.TestCase):

    def test_sqlite_ins_sel(self):
        session = Session.get()
        session.execute("DELETE FROM tagger")
        session.commit()
        session.execute("INSERT INTO tagger VALUES ('foo', 'bar')")
        result = session.query(Tagger)
        for row in result:
            self.assertTrue(row.name == 'foo' and row.version == 'bar')

    def test_is_sqllite(self):
        session = Session.get()
        self.assertTrue(Session.is_sqlite)

    def test_correct_file_exists(self):
        with open(BACKEND_CONFIG) as f:
            config = json.load(f)
        self.assertTrue(os.path.isfile(config["SQLite_path"]))


if __name__ == '__main__':
    unittest.main()
