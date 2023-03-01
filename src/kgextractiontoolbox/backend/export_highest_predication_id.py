import argparse
import logging

from kgextractiontoolbox.backend.database import Session
from kgextractiontoolbox.backend.models import Predication


def export_highest_predication_id(output_file: str):
    """
    Queries the highest predication id from DB and write it to the output file
    :param output_file:
    :return: None
    """
    session = Session.get()
    logging.info(f'Querying highest predication id...')
    highest_predication_id = session.query(Predication.id).order_by(Predication.id.desc()).first()[0]
    logging.info(f'Writing id {highest_predication_id} to {output_file} ...')

    with open(output_file, 'wt') as f:
        f.write(f'{highest_predication_id}')
    logging.info('Finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="Highest predication id will be written to that file")
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    export_highest_predication_id(args.output)


if __name__ == "__main__":
    main()
