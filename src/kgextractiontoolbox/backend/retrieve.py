from collections import defaultdict
from typing import List, Set

from sqlalchemy import and_

import kgextractiontoolbox.document.document
from kgextractiontoolbox.backend.models import Document, DocumentClassification, Tag, DocumentSection, \
    BULK_QUERY_CURSOR_COUNT_DEFAULT, DocumentMetadata, Predication, Sentence
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity, DocumentSection as ds
from kgextractiontoolbox.document.narrative_document import NarrativeDocument, NarrativeDocumentMetadata, \
    StatementExtraction, DocumentSentence


def iterate_over_all_documents_in_collection(session, collection: str, document_ids=None, consider_tag=False,
                                             consider_sections=False, consider_classification=False):
    """
    Iterate over documents in a collection
    :param session: the DB session
    :param collection: document collection
    :param document_ids: a set of document ids as a filter (optional)
    :param consider_tag: should tags be retrieved?
    :param consider_sections: should sections be retrieved?
    :param consider_classification: should classifications be retrieved?
    :return:
    """
    if not collection:
        raise ValueError("Document collection must be specified and cannot be None")

    doc_query = session.query(Document)
    doc_query = doc_query.filter(Document.collection == collection)

    if document_ids:
        document_ids = sorted(list(document_ids))
        doc_query = doc_query.filter(Document.id.in_(document_ids))

    doc_query = doc_query.order_by(Document.id)
    doc_query = doc_query.yield_per(BULK_QUERY_CURSOR_COUNT_DEFAULT)

    if consider_tag:
        tag_query = session.query(Tag)
        tag_query = tag_query.filter(Tag.document_collection == collection)

        if document_ids:
            tag_query = tag_query.filter(Tag.document_id.in_(document_ids))

        tag_query = tag_query.order_by(Tag.document_id)
        tag_query = tag_query.yield_per(BULK_QUERY_CURSOR_COUNT_DEFAULT)
        tag_query = iter(tag_query)
        current_tag = next(tag_query, None)

    if consider_classification:
        class_query = session.query(DocumentClassification)
        class_query = class_query.filter(DocumentClassification.document_collection == collection)

        if document_ids:
            class_query = class_query.filter(DocumentClassification.document_id.in_(document_ids))

        class_query = class_query.order_by(DocumentClassification.document_id)
        class_query = class_query.yield_per(BULK_QUERY_CURSOR_COUNT_DEFAULT)

        class_query = iter(class_query)
        current_class = next(class_query, None)

    if consider_sections:
        sec_query = session.query(DocumentSection)
        sec_query = sec_query.filter(DocumentSection.document_collection == collection)

        if document_ids:
            sec_query = sec_query.filter(DocumentSection.document_id.in_(document_ids))

        sec_query = sec_query.order_by(DocumentSection.document_id)
        sec_query = sec_query.yield_per(BULK_QUERY_CURSOR_COUNT_DEFAULT)
        sec_query = iter(sec_query)
        current_sec = next(sec_query, None)

    for res in doc_query:
        t_doc = TaggedDocument(id=res.id, title=res.title,
                               abstract=res.abstract)

        if consider_tag:
            while current_tag and t_doc.id == current_tag.document_id:
                t_doc.tags.append(TaggedEntity(document=current_tag.document_id,
                                               start=current_tag.start,
                                               end=current_tag.end,
                                               ent_id=current_tag.ent_id,
                                               ent_type=current_tag.ent_type,
                                               text=current_tag.ent_str))
                current_tag = next(tag_query, None)

        if consider_classification:
            while current_class and t_doc.id == current_class.document_id:
                t_doc.classification.update({current_class.classification: current_class.explanation})
                current_class = next(class_query, None)

        if consider_sections:
            while current_sec and t_doc.id == current_sec.document_id:
                t_doc.sections.append(
                    kgextractiontoolbox.document.document.DocumentSection(position=current_sec.position,
                                                                          title=current_sec.title,
                                                                          text=current_sec.text))
                current_sec = next(sec_query, None)

        t_doc.remove_duplicates_and_sort_tags()
        yield t_doc


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

    document_ids = sorted(list(document_ids))
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
        doc_results[doc_id].remove_duplicates_and_sort_tags()

    for doc_id, classification in doc2classification.items():
        doc_results[doc_id].classification = {d_class: d_expl for d_class, d_expl in classification}

    return list(doc_results.values())


def retrieve_narrative_documents_from_database(session, document_ids: Set[int], document_collection: str) \
        -> List[NarrativeDocument]:
    """
    Retrieves a set of Narrative Documents from the database
    :param session: the current session
    :param document_ids: a set of document ids
    :param document_collection: the corresponding document collection
    :return: a list of NarrativeDocuments
    """
    doc_results = {}

    # logging.info(f'Querying {len(document_ids)} from collection: {document_collection}...')
    # first query document titles and abstract
    doc_query = session.query(Document).filter(and_(Document.id.in_(document_ids),
                                                    Document.collection == document_collection))

    for res in doc_query:
        doc_results[res.id] = NarrativeDocument(document_id=res.id, title=res.title, abstract=res.abstract)

    #   logging.info('Querying for document classification...')
    # Next query the publication information
    classification_query = session.query(DocumentClassification).filter(
        and_(DocumentClassification.document_id.in_(document_ids),
             DocumentClassification.document_collection == document_collection))
    doc2classification = defaultdict(set)
    for res in classification_query:
        doc2classification[res.document_id].add((res.classification, res.explanation))

    #    logging.info('Querying for metadata...')
    # Next query the publication information
    metadata_query = session.query(DocumentMetadata).filter(and_(DocumentMetadata.document_id.in_(document_ids),
                                                                 DocumentMetadata.document_collection == document_collection))
    doc2metadata = {}
    for res in metadata_query:
        metadata = NarrativeDocumentMetadata(publication_year=res.publication_year,
                                             publication_month=res.publication_month,
                                             authors=res.authors,
                                             journals=res.journals,
                                             publication_doi=res.publication_doi)
        doc2metadata[res.document_id] = metadata

    # Query for Document sections
    sec_query = session.query(DocumentSection).filter(and_(DocumentSection.document_id.in_(document_ids),
                                                           DocumentSection.document_collection == document_collection))
    for res_sec in sec_query:
        doc_results[res_sec.document_id].sections.append(ds(
            position=res_sec.position,
            title=res_sec.title,
            text=res_sec.text
        ))
    #  logging.info('Querying for tags...')
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

    # logging.info('Querying for statement extractions...')
    # Next query for extracted statements
    es_query = session.query(Predication).filter(and_(Predication.document_id.in_(document_ids),
                                                      Predication.document_collection == document_collection))
    es_for_doc = defaultdict(list)
    sentence_ids = set()
    sentenceid2doc = defaultdict(set)
    for res in es_query:
        es_for_doc[res.document_id].append(StatementExtraction(subject_id=res.subject_id,
                                                               subject_type=res.subject_type,
                                                               subject_str=res.subject_str,
                                                               predicate=res.predicate,
                                                               relation=res.relation,
                                                               object_id=res.object_id,
                                                               object_type=res.object_type,
                                                               object_str=res.object_str,
                                                               sentence_id=res.sentence_id,
                                                               confidence=res.confidence))
        sentence_ids.add(res.sentence_id)
        sentenceid2doc[res.sentence_id].add(res.document_id)

    for doc_id, extractions in es_for_doc.items():
        doc_results[doc_id].extracted_statements = extractions

    # logging.info('Querying for sentences...')
    # Last query for document sentences
    sentence_query = session.query(Sentence).filter(Sentence.id.in_(sentence_ids))
    doc2sentences = defaultdict(list)
    for res in sentence_query:
        for doc_id in sentenceid2doc[res.id]:
            doc2sentences[doc_id].append(DocumentSentence(sentence_id=res.id, text=res.text))

    for doc_id, sentences in doc2sentences.items():
        doc_results[doc_id].sentences = sentences

    for doc_id, metadata in doc2metadata.items():
        doc_results[doc_id].metadata = metadata

    for doc_id, classification in doc2classification.items():
        doc_results[doc_id].classification = {d_class: d_expl for d_class, d_expl in classification}

    return list(doc_results.values())
