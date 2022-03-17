from collections import defaultdict
from typing import List, Set

from sqlalchemy import and_

import kgextractiontoolbox.document.document
from kgextractiontoolbox.backend.models import Document, DocumentClassification, Tag, DocumentSection, \
    BULK_QUERY_CURSOR_COUNT_DEFAULT
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity


def iterate_over_documents_in_collection(session, collection: str, consider_sections=False):
    if consider_sections:
        doc_query = session.query(Document).filter(Document.collection == collection) \
            .order_by(Document.id) \
            .yield_per(BULK_QUERY_CURSOR_COUNT_DEFAULT)

        sec_query = session.query(DocumentSection).filter(DocumentSection.document_collection == collection) \
            .order_by(DocumentSection.document_id) \
            .yield_per(BULK_QUERY_CURSOR_COUNT_DEFAULT)
        sec_query = iter(sec_query)
        current_sec = next(sec_query)

        for res in doc_query:
            t_doc = TaggedDocument(id=res.id, title=res.title,
                                   abstract=res.abstract)
            while current_sec and t_doc.id == current_sec.document_id:
                t_doc.sections.append(
                    kgextractiontoolbox.document.document.DocumentSection(position=current_sec.position,
                                                                          title=current_sec.title,
                                                                          text=current_sec.text))
                current_sec = next(sec_query)

            yield t_doc

    else:
        doc_query = session.query(Document).filter(Document.collection == collection) \
            .yield_per(BULK_QUERY_CURSOR_COUNT_DEFAULT)
        for res in doc_query:
            yield TaggedDocument(id=res.id, title=res.title,
                                 abstract=res.abstract)


def retrieve_tagged_documents_from_database(session, document_ids: Set[int], document_collection: str) \
        -> List[TaggedDocument]:
    """
    Retrieves a set of TaggedDocuments from the database
    :param session: the current session
    :param document_ids: a set of document ids
    :param document_collection: the corresponding document collection
    :return: a list of TaggedDocuments
    """
    doc_results = {}

    # first query document titles and abstract
    doc_query = session.query(Document).filter(and_(Document.id.in_(document_ids),
                                                    Document.collection == document_collection))

    for res in doc_query:
        doc_results[res.id] = TaggedDocument(id=res.id, title=res.title, abstract=res.abstract)

    # Next query the publication information
    classification_query = session.query(DocumentClassification).filter(
        and_(DocumentClassification.document_id.in_(document_ids),
             DocumentClassification.document_collection == document_collection))
    doc2classification = defaultdict(set)
    for res in classification_query:
        doc2classification[res.document_id].add((res.classification, res.explanation))

    # Query for Document sections
    sec_query = session.query(DocumentSection).filter(and_(DocumentSection.document_id.in_(document_ids),
                                                           DocumentSection.document_collection == document_collection))
    for res_sec in sec_query:
        doc_results[res_sec.document_id].sections.append(kgextractiontoolbox.document.document.DocumentSection(
            position=res_sec.position,
            title=res_sec.title,
            text=res_sec.text
        ))

    # Next query for all tagged entities in that document
    tag_query = session.query(Tag).filter(and_(Tag.document_id.in_(document_ids),
                                               Tag.document_collection == document_collection))
    tag_result = defaultdict(list)
    for res in tag_query:
        tag_result[res.document_id].append(TaggedEntity(document=res.document_id,
                                                        start=res.start,
                                                        end=res.end,
                                                        ent_id=res.ent_id,
                                                        ent_type=res.ent_type,
                                                        text=res.ent_str))
    for doc_id, tags in tag_result.items():
        doc_results[doc_id].tags = tags
        doc_results[doc_id].sort_tags()

    for doc_id, classification in doc2classification.items():
        doc_results[doc_id].classification = {d_class: d_expl for d_class, d_expl in classification}

    return list(doc_results.values())
