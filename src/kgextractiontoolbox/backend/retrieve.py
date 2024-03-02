import logging
from collections import defaultdict
from typing import List, Set

import kgextractiontoolbox.document.document
from kgextractiontoolbox.backend.models import Document, DocumentClassification, Tag, DocumentSection, \
    DocumentMetadata, Predication, Sentence
from kgextractiontoolbox.document.document import TaggedDocument, TaggedEntity
from kgextractiontoolbox.document.narrative_document import NarrativeDocument, NarrativeDocumentMetadata, \
    StatementExtraction, DocumentSentence


def should_use_range_mode(document_ids: List[int]) -> (bool, int, int):
    """
    if the diff between highest and lowest id corresponds to the number of document ids
    a range query should be way faster than a large IN expression
    note that we do not ensure that all ids are given (so 20% of missing documents in between are ok)
    :param document_ids: a sorted list of document ids
    :return:
    """
    highest_id = document_ids[-1]
    lowest_id = document_ids[0]
    if lowest_id > highest_id:
        raise ValueError(f'Document id list must be supported')

    if 1000 < len(document_ids) and len(document_ids) > (highest_id - lowest_id) * 0.8:
        logging.info(f"Using fast range mode to filter for document ids ({lowest_id} - {highest_id})")
        return True, lowest_id, highest_id
    else:
        return False, lowest_id, highest_id


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
        enable_range_mode, lowest_id, highest_id = should_use_range_mode(document_ids)

        if enable_range_mode:
            # ensure that we have ids here
            document_ids_set = set({int(did) for did in document_ids})
            doc_query = doc_query.filter(Document.id.between(lowest_id, highest_id))
        else:
            doc_query = doc_query.filter(Document.id.in_(document_ids))

    doc_query = doc_query.order_by(Document.id)

    if consider_tag:
        tag_query = session.query(Tag)
        tag_query = tag_query.filter(Tag.document_collection == collection)

        if document_ids:
            if enable_range_mode:
                tag_query = tag_query.filter(Tag.document_id.between(lowest_id, highest_id))
            else:
                tag_query = tag_query.filter(Tag.document_id.in_(document_ids))

        tag_query = tag_query.order_by(Tag.document_id)
        tag_query = iter(tag_query)
        current_tag = next(tag_query, None)

    if consider_classification:
        class_query = session.query(DocumentClassification)
        class_query = class_query.filter(DocumentClassification.document_collection == collection)

        if document_ids:
            if enable_range_mode:
                class_query = class_query.filter(DocumentClassification.document_id.between(lowest_id, highest_id))
            else:
                class_query = class_query.filter(DocumentClassification.document_id.in_(document_ids))

        class_query = class_query.order_by(DocumentClassification.document_id)

        class_query = iter(class_query)
        current_class = next(class_query, None)

    if consider_sections:
        sec_query = session.query(DocumentSection)
        sec_query = sec_query.filter(DocumentSection.document_collection == collection)

        if document_ids:
            if enable_range_mode:
                sec_query = sec_query.filter(DocumentSection.document_id.between(lowest_id, highest_id))
            else:
                sec_query = sec_query.filter(DocumentSection.document_id.in_(document_ids))

        sec_query = sec_query.order_by(DocumentSection.document_id)
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

        # if we queried with a range mode, we need to ensure that the document ids are really needed
        if document_ids and enable_range_mode:
            if t_doc.id in document_ids_set:
                yield t_doc
        else:
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
    enable_range_mode, lowest_id, highest_id = should_use_range_mode(document_ids)

    # first query document titles and abstract
    doc_query = session.query(Document)
    doc_query = doc_query.filter(Document.collection == document_collection)
    if enable_range_mode:
        # ensure that we have ids here
        document_ids_set = set({int(did) for did in document_ids})
        doc_query = doc_query.filter(Document.id.between(lowest_id, highest_id))
    else:
        doc_query = doc_query.filter(Document.id.in_(document_ids))

    for res in doc_query:
        if enable_range_mode and res.id not in document_ids_set:
            continue
        doc_results[res.id] = TaggedDocument(id=res.id, title=res.title, abstract=res.abstract)

    # Next query the classification information
    classification_query = session.query(DocumentClassification)
    classification_query = classification_query.filter(
        DocumentClassification.document_collection == document_collection)

    if enable_range_mode:
        classification_query = classification_query.filter(
            DocumentClassification.document_id.between(lowest_id, highest_id))
    else:
        classification_query = classification_query.filter(DocumentClassification.document_id.in_(document_ids))

    doc2classification = defaultdict(set)
    for res in classification_query:
        if enable_range_mode and res.document_id not in document_ids_set:
            continue
        doc2classification[res.document_id].add((res.classification, res.explanation))

    # Query for Document sections
    sec_query = session.query(DocumentSection)
    sec_query = sec_query.filter(DocumentSection.document_collection == document_collection)

    if enable_range_mode:
        sec_query = sec_query.filter(DocumentSection.document_id.between(lowest_id, highest_id))
    else:
        sec_query = sec_query.filter(DocumentSection.document_id.in_(document_ids))

    for res_sec in sec_query:
        if enable_range_mode and res_sec.document_id not in document_ids_set:
            continue

        doc_results[res_sec.document_id].sections.append(kgextractiontoolbox.document.document.DocumentSection(
            position=res_sec.position,
            title=res_sec.title,
            text=res_sec.text
        ))

    # Next query for all tagged entities in that document
    tag_query = session.query(Tag)
    tag_query = tag_query.filter(Tag.document_collection == document_collection)
    if enable_range_mode:
        tag_query = tag_query.filter(Tag.document_id.between(lowest_id, highest_id))
    else:
        tag_query = tag_query.filter(Tag.document_id.in_(document_ids))

    tag_result = defaultdict(list)
    for res in tag_query:
        if enable_range_mode and res.document_id not in document_ids_set:
            continue

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
    tagged_docs = retrieve_tagged_documents_from_database(session, document_ids, document_collection)

    doc_results = {d.id: NarrativeDocument(document_id=d.id,
                                           title=d.title,
                                           abstract=d.abstract,
                                           tags=d.tags,
                                           classification=d.classification,
                                           sections=d.sections) for d in tagged_docs}

    document_ids = sorted(list(document_ids))
    enable_range_mode, lowest_id, highest_id = should_use_range_mode(document_ids)

    # Next query the metadata information
    metadata_query = session.query(DocumentMetadata)
    metadata_query = metadata_query.filter(DocumentMetadata.document_collection == document_collection)
    if enable_range_mode:
        metadata_query = metadata_query.filter(DocumentMetadata.document_id.between(lowest_id, highest_id))
    else:
        metadata_query = metadata_query.filter(DocumentMetadata.document_id.in_(document_ids))

    doc2metadata = {}
    for res in metadata_query:
        if enable_range_mode and res.document_id not in doc_results:
            continue
        metadata = NarrativeDocumentMetadata(publication_year=res.publication_year,
                                             publication_month=res.publication_month,
                                             authors=res.authors,
                                             journals=res.journals,
                                             publication_doi=res.publication_doi)
        doc2metadata[res.document_id] = metadata

    # Next query for extracted statements
    es_query = session.query(Predication)
    es_query = es_query.filter(Predication.document_collection == document_collection)
    es_query = es_query.filter(Predication.document_id.in_(document_ids))

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

    return list(doc_results.values())
