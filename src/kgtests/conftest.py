import os
import shutil
from pathlib import Path

from kgextractiontoolbox.backend.database import Session
from kgtests.util import tmp_rel_path

from narraint import config as config2
from kgextractiontoolbox import config as config3
from narrant import config


def pytest_sessionstart(session):
    # Override global configuration vars
    import kgextractiontoolbox.config
    backend_config = Path(kgextractiontoolbox.config.GIT_ROOT_DIR) / "src/kgtests/config/jsonfiles/backend.json"

    config.BACKEND_CONFIG = backend_config
    config2.BACKEND_CONFIG = config.BACKEND_CONFIG
    config3.BACKEND_CONFIG = config.BACKEND_CONFIG

    print(f"backend_config: {backend_config}")
    shutil.rmtree(tmp_rel_path(""), ignore_errors=True)
    os.makedirs(tmp_rel_path(""))
    sql_session = Session.get(str(backend_config))
