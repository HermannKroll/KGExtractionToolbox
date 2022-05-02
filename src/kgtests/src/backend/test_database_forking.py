import unittest

import multiprocessing

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Tagger


class TestDatabaseForking(unittest.TestCase):

    def test_database_forking(self):
        def process_run():
            s2 = Session.get()
            for r in s2.query(Tagger):
                print(f'process: {r.name}')

        session = Session.get()
        values = [dict(name='Tagger1', version="1.0.0")]
        Tagger.bulk_insert_values_into_table(session, values)

        for r in session.query(Tagger):
            print(f'{r.name}')

        session.remove()

        processes = []
        for i in range(0, 5):
            process = multiprocessing.Process(target=process_run)
            process.start()
            processes.append(process)

        for process in processes:
            process.join(timeout=10)
