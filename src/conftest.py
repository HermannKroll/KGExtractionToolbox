import os
import shutil

from kgextractiontoolbox import config as config3
from narraint import config as config2
from narraint.backend.database import SessionExtended
from narrant import config
from nitests.util import tmp_rel_path

ENTITY_TEST_CONFIG_CONTENT = """
{
  "pmcid2pmid": "/home/kroll/tools/pmcid2pmid.tsv",
  "pmc_dir": "/hdd2/datasets/pubmed_central",
  "taggerOne": {
    "root": "/home/kroll/tools/tagger/TaggerOne-0.2.1",
    "model": "models/model_BC5CDRJ_011.bin",
    "batchSize": 10000,
    "timeout": 10,
    "max_retries": 1
  },
  "gnormPlus": {
    "root": "/home/kroll/tools/tagger/GNormPlusJava",
    "javaArgs": "-Xmx100G -Xms30G"
  },
  "dnorm": "/home/kroll/tools/tagger/DNorm-0.0.7",
  "tmchem": "/home/kroll/tools/tagger/tmChemM1-0.0.2",
  "dict": {
    "max_words": 5,
    "check_abbreviation": "true",
    "custom_abbreviations": "true",
    "min_full_tag_len": 5
  },
  "drug": {
    "check_products": 0,
    "max_per_product": 2,
    "min_name_length": 3,
    "ignore_excipient_terms": 1
  }
}
"""


def pytest_sessionstart(session):
    # Override global configuration vars
    print('removing test tmp dir...')
    shutil.rmtree(tmp_rel_path(""), ignore_errors=True)
    os.makedirs(tmp_rel_path(""))

    print('writing test configs...')
    backend_config = tmp_rel_path("test_backend.json")
    backend_db = tmp_rel_path("test.db")

    config_content = '{"use_SQLite": true, "SQLite_path": "' + backend_db + '"}'
    with open(backend_config, 'wt') as f:
        f.write(config_content)

    config.BACKEND_CONFIG = backend_config
    config2.BACKEND_CONFIG = config.BACKEND_CONFIG
    config3.BACKEND_CONFIG = config.BACKEND_CONFIG

    el_config = tmp_rel_path("entity_linking.json")
    with open(el_config, 'wt') as f:
        f.write(ENTITY_TEST_CONFIG_CONTENT)

    config.PREPROCESS_CONFIG = el_config
    config3.ENTITY_LINKING_CONFIG = el_config

    print(f"backend_config: {backend_config}")
    sql_session = SessionExtended.get(backend_config)
