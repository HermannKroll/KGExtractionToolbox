import argparse
import logging
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.cimmutabledict import immutabledict

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication, PredicationToDelete
from kgextractiontoolbox.cleaning.relation_type_constraints import RelationTypeConstraintStore
from kgextractiontoolbox.progress import print_progress_with_eta

BULK_QUERY_CURSOR_COUNT = 100000


def clean_predication_to_delete_table(session):
    """
    Clean all entries in the PredicationToDelete table
    :param session: the current session
    :return: None
    """
    logging.debug('Cleaning Predication To Delete Table...')
    stmt = delete(PredicationToDelete)
    session.execute(stmt)
    logging.debug('Committing...')
    session.commit()


def delete_predications_hurting_type_constraints(relation_type_constraints: RelationTypeConstraintStore,
                                                 document_collection: str = None,
                                                 reorder_tuples_if_allowed=False,
                                                 predicate_id_minimum: int = None):
    """
    Checks the type constraints
    If subject and object could be swapped to meet the constraint - they will be swapped
    Otherwise the extraction will be mapped to associate
    :param relation_type_constraints: the relation type constraint store
    :param document_collection: apply constraints only for this document collection
    :param reorder_tuples_if_allowed: if type constraints are hurt but a swapping of s and o would solve it,
    the tuple will be flipped if this parameter is true
    :param predicate_id_minimum: only predication ids above this id will be considered
    :return: None
    """
    preds_to_delete = set()
    preds_to_reorder = set()

    session = Session.get()
    clean_predication_to_delete_table(session)
    logging.info('Counting the number of predications...')
    pred_count_q = session.query(Predication)
    if document_collection:
        logging.info(f'Consider only in collection {document_collection}')
        pred_count_q = pred_count_q.filter(Predication.document_collection == document_collection)

    if predicate_id_minimum:
        logging.info(f'Consider only predication ids >= {predicate_id_minimum}')
        pred_count_q = pred_count_q.filter(Predication.id >= predicate_id_minimum)

    pred_count = pred_count_q.count()
    logging.info(f'{pred_count} predications were found')
    logging.info('Querying predications...')
    pred_query = session.query(Predication).filter(Predication.relation != None)
    if document_collection:
        pred_query = pred_query.filter(Predication.document_collection == document_collection)
    if predicate_id_minimum:
        logging.info(f'Consider only predication ids >= {predicate_id_minimum}')
        pred_query = pred_query.filter(Predication.id >= predicate_id_minimum)
    pred_query = pred_query.yield_per(BULK_QUERY_CURSOR_COUNT)
    start_time = datetime.now()
    for idx, pred in enumerate(pred_query):
        print_progress_with_eta("checking type constraints", idx, pred_count, start_time)
        if pred.relation in relation_type_constraints.constraints:
            s_types = relation_type_constraints.get_subject_constraints(pred.relation)
            o_types = relation_type_constraints.get_object_constraints(pred.relation)
            if pred.subject_type not in s_types or pred.object_type not in o_types:
                if reorder_tuples_if_allowed:
                    if pred.subject_type in o_types and pred.object_type in s_types:
                        # Flipping will solve the problem - reorder the tuple
                        preds_to_reorder.add(pred.id)
                    else:
                        # Flipping won't solve the problem - delete it
                        preds_to_delete.add(pred.id)
                else:
                    # arguments hurt type constraints
                    preds_to_delete.add(pred.id)

    logging.info(f'Deleting {len(preds_to_delete)} predications...')
    values_to_delete = []
    for id_to_delete in preds_to_delete:
        values_to_delete.append(dict(predication_id=id_to_delete))
    PredicationToDelete.bulk_insert_values_into_table(session, values_to_delete, check_constraints=False)
    subquery = session.query(PredicationToDelete.predication_id).subquery()
    stmt = delete(Predication).where(Predication.id.in_(subquery))
    session.execute(stmt, execution_options=immutabledict({"synchronize_session": 'fetch'}))
    logging.debug('Committing...')
    session.commit()
    clean_predication_to_delete_table(session)

    if reorder_tuples_if_allowed and len(preds_to_reorder) > 0:
        logging.info(f'Reordering {len(preds_to_reorder)} predication subject and objects...')
        values_to_reorder = []
        for id_to_reorder in preds_to_reorder:
            values_to_reorder.append(dict(predication_id=id_to_reorder))
        PredicationToDelete.bulk_insert_values_into_table(session, values_to_reorder, check_constraints=False)
        subquery = session.query(PredicationToDelete.predication_id).subquery()
        pred_query = session.query(Predication).filter(Predication.id.in_(subquery)) \
            .yield_per(BULK_QUERY_CURSOR_COUNT)
        predication_values = []
        start_time = datetime.now()
        for idx, pred in enumerate(pred_query):
            print_progress_with_eta("reorder subject and objects...", idx, pred_count, start_time)
            predication_values.append(dict(
                document_id=pred.document_id,
                document_collection=pred.document_collection,
                object_id=pred.subject_id,
                object_str=pred.subject_str,
                object_type=pred.subject_type,
                predicate=pred.predicate,
                relation=pred.relation,
                subject_id=pred.object_id,
                subject_str=pred.object_str,
                subject_type=pred.object_type,
                confidence=pred.confidence,
                sentence_id=pred.sentence_id,
                extraction_type=pred.extraction_type
            ))

        logging.info(f'Insert {len(predication_values)} reordered predications to database')
        Predication.bulk_insert_values_into_table(session, predication_values, check_constraints=False)
        logging.info(f'Deleting {len(preds_to_reorder)} old and wrongly ordered predications')
        subquery = session.query(PredicationToDelete.predication_id).subquery()
        stmt = delete(Predication).where(Predication.id.in_(subquery))
        session.execute(stmt, execution_options=immutabledict({"synchronize_session": 'fetch'}))
        logging.debug('Committing...')
        session.commit()
        clean_predication_to_delete_table(session)


def main():
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("constraint_file", help='Path to the relation constraint JSON file')
    parser.add_argument("-c", "--collection", required=False, help='Apply constraints only in this document collection')
    parser.add_argument("--allow_reorder", action="store_true", required=False,
                        help='Will reorder tuples that hurt type constraints if possible')
    parser.add_argument("--predicate_id_minimum", default=None, type=int, required=False,
                        help="only predication ids above this will be considered")

    args = parser.parse_args()
    constraints = RelationTypeConstraintStore()
    logging.info(f'Loading constraints from {args.constraint_file}')
    constraints.load_from_json(args.constraint_file)
    logging.info('Checking type constraints...')
    delete_predications_hurting_type_constraints(constraints, document_collection=args.collection,
                                                 reorder_tuples_if_allowed=args.allow_reorder,
                                                 predicate_id_minimum=args.predicate_id_minimum)
    logging.info('Finished...')


if __name__ == "__main__":
    main()
