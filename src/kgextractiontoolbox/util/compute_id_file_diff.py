import argparse
import logging


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("idfile1", help="The first id file  (plain file with document ids in each line)")
    parser.add_argument("idfile2", help="The second id file (plain file with document ids in each line)")
    parser.add_argument("output", help="ids1 - ids2 will be written to this file (plain file with ids in each line)")
    args = parser.parse_args(args)

    logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d:%H:%M:%S',
                        level=logging.INFO)

    logging.info(f'Reading ids from file: {args.idfile1}')
    with open(args.idfile1, "rt") as f:
        document_ids_1 = set([int(line.strip()) for line in f])
    logging.info(f'{len(document_ids_1)} ids found')

    logging.info(f'Reading ids from file: {args.idfile2}')
    with open(args.idfile2, "rt") as f:
        document_ids_2 = set([int(line.strip()) for line in f])
    logging.info(f'{len(document_ids_2)} ids found')

    logging.info('Computing difference (idfile1 - idfile2)')
    diff_ids = document_ids_1 - document_ids_2
    logging.info(f'{len(diff_ids)} ids remaining')

    logging.info(f'Writing {len(diff_ids)} to {args.output}...')
    with open(args.output, 'wt') as f:
        f.write('\n'.join([str(d) for d in diff_ids]))
    logging.info('Finished')


if __name__ == "__main__":
    main()
