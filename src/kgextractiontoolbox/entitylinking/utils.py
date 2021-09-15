import logging

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import DocTaggedBy
from kgextractiontoolbox.document.document import TaggedDocument
from kgextractiontoolbox.document.regex import DOCUMENT_ID


class DocumentError(Exception):
    pass


def get_document_id(fn):
    with open(fn) as f:
        line = f.readline()
    try:
        match = DOCUMENT_ID.match(line)
        if match:
            return int(match.group(1))
        else:
            doc = TaggedDocument(fn)
            return doc.id
    except AttributeError:
        raise DocumentError(f"No ID found for {fn}")


def get_untagged_doc_ids_by_ent_type(collection, target_ids, ent_type, tagger_cls, logger):
    session = Session.get()
    result = session.query(DocTaggedBy).filter(
        DocTaggedBy.document_collection == collection,
        DocTaggedBy.ent_type == ent_type,
        DocTaggedBy.tagger_name == tagger_cls.__name__,
        DocTaggedBy.tagger_version == tagger_cls.__version__,
    ).values(DocTaggedBy.document_id)
    present_ids = set(x[0] for x in result)
    logger.debug(
        "Retrieved {} ids (ent_type={},collection={},tagger={}/{})".format(
            len(present_ids), ent_type, collection, tagger_cls.__name__, tagger_cls.__version__
        ))
    missing_ids = target_ids.difference(present_ids)
    return missing_ids


LOGGING_FORMAT = '%(asctime)s %(levelname)s %(threadName)s %(module)s:%(lineno)d %(message)s'


def init_preprocess_logger(log_filename, log_level, log_format=LOGGING_FORMAT, worker_id: int = None):
    formatter = logging.Formatter(log_format)
    logger = logging.getLogger("preprocess" if worker_id is None else f"preprocess-w{worker_id}")
    logger.setLevel("DEBUG")
    logger.propagate = False
    fh = logging.FileHandler(log_filename, mode="a+")
    fh.setLevel("DEBUG")
    fh.setFormatter(formatter)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def init_sqlalchemy_logger(log_filename, log_level=logging.INFO):
    formatter = logging.Formatter(LOGGING_FORMAT)
    logger = logging.getLogger('sqlalchemy.engine')
    logger.setLevel(log_level)
    logger.propagate = False
    fh = logging.FileHandler(log_filename, mode="a+")
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
