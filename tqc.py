import os
import sys
import csv
import time
import json
import requests
import argparse
import pandas as pd
from datetime import datetime, timedelta


def required_add_columns():
    '''
    Columns required for adding data to TQC.
    '''
    return [
        'central_sample_id', 
        'run_name', 
        'pag_name'
    ]


def returned_get_columns():
    '''
    Columns displayed by getting data from TQC.
    '''
    return [
        'central_sample_id', 
        'run_name',
        'pag_name',
        'sequencing_org_code',
        'meta.foel.producer',
        'meta.phe.private-provider',
        'meta.phe.site',
        'collection_pillar',
        'collection_date', 
        'received_date', 
        'sequencing_org_received_date', 
        'sequencing_submission_date',
        'published_date',
        'fasta_path',
        'num_bases',
        'pc_acgt',
        'pc_masked',
        'pc_ambiguous', 
        'pc_invalid', 
        'longest_gap', 
        'longest_ungap',
        'bam_path',
        'library_primers',
        'library_primers_reported', 
        'num_pos', 
        'mean_cov', 
        'pc_pos_cov_gte1', 
        'pc_pos_cov_gte5',
        'pc_pos_cov_gte10', 
        'pc_pos_cov_gte20', 
        'pc_pos_cov_gte50',
        'pc_pos_cov_gte100',
        'pc_pos_cov_gte200',
        'pc_tiles_medcov_gte1', 
        'pc_tiles_medcov_gte5', 
        'pc_tiles_medcov_gte10', 
        'pc_tiles_medcov_gte20', 
        'pc_tiles_medcov_gte50', 
        'pc_tiles_medcov_gte100', 
        'pc_tiles_medcov_gte200', 
        'tile_n', 
        'tile_vector',
        'pag_suppressed',
        'pag_basic_qc',
    ]


def numeric_columns():
    '''
    Columns in TQC with cells of type int/float.
    '''
    return [
        'num_bases',
        'pc_acgt',
        'pc_masked',
        'pc_ambiguous',
        'pc_invalid', 
        'longest_gap', 
        'longest_ungap',
        'num_pos', 
        'mean_cov', 
        'pc_pos_cov_gte1', 
        'pc_pos_cov_gte5',
        'pc_pos_cov_gte10', 
        'pc_pos_cov_gte20', 
        'pc_pos_cov_gte50',
        'pc_pos_cov_gte100',
        'pc_pos_cov_gte200',
        'pc_tiles_medcov_gte1', 
        'pc_tiles_medcov_gte5', 
        'pc_tiles_medcov_gte10', 
        'pc_tiles_medcov_gte20', 
        'pc_tiles_medcov_gte50', 
        'pc_tiles_medcov_gte100', 
        'pc_tiles_medcov_gte200', 
        'tile_n'
    ]


def date_columns():
    '''
    Columns in TQC containing date information.
    '''
    return [
        'collection_date', 
        'received_date', 
        'sequencing_org_received_date', 
        'sequencing_submission_date', 
        'published_date'
    ]


def column_aliases(mode):
    '''
    Fields that need renaming when adding/getting from TQC.

    `mode` takes either 'add' or 'get' and returns the corresponding dictionary mapping.
    '''
    aliases = {
        'meta.foel.producer' : 'foel_producer',
        'meta.phe.private-provider' : 'phe_private_provider',
        'meta.phe.site' : 'phe_site'
    }
    
    if mode == 'add':
        return aliases
    elif mode == 'get':
        # Invert dictionary
        return {v : k for k, v in aliases.items()}
    else:
        raise Exception('Incorrect mode passed to column_aliases')


def operators():
    '''
    Operators on numeric fields in TQC.
    '''
    return [
        'lt', 
        'gt', 
        'leq', 
        'geq', 
        'eq', 
        'neq'
    ]


def empty_cell():
    '''
    Character for matching empty cells.
    '''
    return '_'


def add(url, api_key, tsv_path, print_uploads=True):
    start = time.time()

    if tsv_path == '-':
        tsv = sys.stdin
    else:
        tsv = open(tsv_path)

    attempted = 0
    successful = 0
    failed = 0

    try:
        reader = csv.DictReader(tsv, delimiter='\t')
        columns = reader.fieldnames
        if columns:
            for x in required_add_columns():
                if not (x in set(columns)):
                    raise Exception(f"'{x}' column is missing")
            
            request_url = f'{url}/add'
            headers = {'api_key': api_key}

            with open(f"{os.getenv('EAGLEOWL_SCRATCH')}/tqc/failures.log", "a") as failures:
                # Iterate through tsv table
                for record in reader:
                    for name, replacement in column_aliases('add').items():
                        if record.get(name):
                            record[replacement] = record.pop(name)

                    # Convert to json string
                    payload = json.dumps(record)
                    # Post the json
                    response = requests.post(request_url, data=payload, headers=headers)
                    # (Optionally) print upload
                    if print_uploads:
                        print(f'{response}: {response.reason}, id: {record["central_sample_id"]}, run: {record["run_name"]}, pag: {record["pag_name"]}')
                    
                    attempted += 1
                    if response.ok:
                        successful += 1
                    else:
                        # First failure is marked with the date
                        if failed == 0:
                            failures.write(datetime.today().strftime('%Y-%m-%d') + '\n')
                        failed += 1
                        failures.write(payload + '\n')
    finally:
        if tsv is not sys.stdin:
            tsv.close()

        end = time.time()

        print('[UPLOADS]')
        print(f'Attempted: {attempted}')
        print(f'Successful: {successful}')
        print(f'Failed: {failed}')
        print('[TIME]')
        print(f'{int((end - start) // 60)} m {round((end - start) % 60, 2)} s')


def make_query_params(args, pag_defaults=True):

    if pag_defaults == True:
        # Default for pag_suppressed
        if args.get('pag_suppressed') is None:
            args['pag_suppressed'] = ['VALID']
        
        for i, x in enumerate(args['pag_suppressed']):
            args['pag_suppressed'][i] = x.upper()

        # Default for pag_basic_qc
        if args.get('pag_basic_qc') is None:
            args['pag_basic_qc'] = ['PASS']
        
        for i, x in enumerate(args['pag_basic_qc']):
            args['pag_basic_qc'][i] = x.upper()
    else:
        args['pag_suppressed'] = None
        args['pag_basic_qc'] = None
    
    # Remove all keyword arguments that were passed with a value of None
    args = {arg : value for arg, value in args.items() if value is not None}

    date_args = date_columns()
    numeric_args = numeric_columns()

    date_range_args = [x + '_range' for x in date_args]
    iso_week_args = [x[:-len('_date')] + '_iso_week' for x in date_args]
    iso_week_range_args = [x[:-len('_date')] + '_iso_week_range' for x in date_args]

    params = []
    # Move through the values and append them to the list
    for arg, value in args.items():
        # Handle date arguments
        if arg in date_args:
            for val in value:
                # If a 'today' is given, match rows with cells containing today's date
                if val.lower() == 'today':
                    val = datetime.today().strftime('%Y-%m-%d')
                # Match rows with empty cells for that field
                elif val == empty_cell():
                    val = ''
                params.append(f'{arg}={val}')

        # Handle ISO week arguments
        elif arg in iso_week_args:
            for val in value:
                year, week = val.split('-')
                dates = [datetime.fromisocalendar(int(year), int(week), i).strftime('%Y-%m-%d') for i in range(1, 8)]
                for date in dates:
                    params.append(f'{arg[:-len("_iso_week")] + "_date"}={date}')

        # Handle date range arguments (all dates within two dates, inclusive)
        elif arg in date_range_args:
            # TODO: test
            if value[0].lower() == 'today':
                start_date = datetime.today().date()
            else:
                start_date = datetime.strptime(value[0], '%Y-%m-%d').date()
            
            if value[1].lower() == 'today':
                end_date = datetime.today().date()
            else:
                end_date = datetime.strptime(value[1], '%Y-%m-%d').date()
            difference = (end_date - start_date).days
            
            if difference < 0:
                raise Exception(f'{arg}: end_date is less than start_date')

            dates = []
            for i in range(difference + 1):
                dates.append(start_date + timedelta(days=i))
            for date in dates:
                params.append(f'{arg[:-len("_range")]}={date}')
        
        # Handle ISO week range arguments (all dates within two iso weeks, inclusive)
        elif arg in iso_week_range_args:
            year1, week1 = value[0].split('-')
            year2, week2 = value[1].split('-')
            start_date = datetime.fromisocalendar(int(year1), int(week1), 1).date()
            end_date = datetime.fromisocalendar(int(year2), int(week2), 7).date()
            difference = (end_date - start_date).days

            if difference < 0:
                raise Exception(f'{arg}: end_date is less than start_date')

            dates = []
            for i in range(difference + 1):
                dates.append(start_date + timedelta(days=i))
            for date in dates:
                params.append(f'{arg[:-len("_iso_week_range")] + "_date"}={date}')
        
        # Handle numeric arguments
        elif arg in numeric_args:
            for val in value:
                operator, num = val

                # Validate before firing at the database
                if not (operator.lower() in operators()):
                    raise Exception(f'\'{operator}\' is not an operator')
                try:
                    num = int(num)
                except ValueError:
                    try:
                        num = float(num)
                    except ValueError:
                        raise Exception(f'Encountered non-numeric value \'{num}\' in numeric argument \'{arg}\'')

                params.append(f'{arg}={operator}_{num}')

        # Handle all other arguments
        else:
            for val in value:
                # Match rows with empty cells for that field
                if val == empty_cell():
                    val = ''
                params.append(f'{arg}={val}')
    
    # The returned string will be attached to the get query
    return '&'.join(params)


def read_records(path):
    records = []
    with open(path) as tsv:
        reader = csv.DictReader(tsv, delimiter='\t')
        if not reader.fieldnames:
            raise Exception('Failed to read fieldnames from input file')
        for row in reader:
            new_row = {field : row[field].strip() for field in reader.fieldnames}
            if new_row:
                records.append(new_row)
    return records


def get(url, args, metadata_path=None, pag_defaults=None):
    request_url = f'{url}/get'
    params = make_query_params(args, pag_defaults=pag_defaults)

    # If any parameters have been passed to filter on
    if params:
        request_url += '/?' + params        

    # Get response and store in dataframe
    response = requests.get(request_url)

    if not response.ok:
        print(f'{response}: {response.reason}. {json.loads(response.text).get("detail")}')
    else:
        df = pd.json_normalize(json.loads(response.text))
        # If we have a non-empty search result
        if list(df.columns.values):
            # Delete id column from the dataframe
            df = df.drop('id', axis=1)
            # Rename columns
            df = df.rename(columns=column_aliases('get')) # type: ignore
            # Reorder columns
            df = df[returned_get_columns()]

            # Annotate the TQC output table with additional metadata, if it was supplied
            if metadata_path:
                metadata = pd.DataFrame.from_records(read_records(metadata_path))
                metadata = metadata.rename({'library_primers' : 'meta.library_primers'}, axis=1)
                df = df.merge(metadata, on=list(metadata.columns.intersection(df.columns)), how='left')
            
            # Print the data
            print(df.to_csv(index=False, sep='\t'), end='')
        else:
            # Print an empty table
            print('\t'.join(returned_get_columns()))


def main():
    parser = argparse.ArgumentParser()
    request_parsers = parser.add_subparsers(dest='request_type', required=True)
    
    # Add request
    add_parser = request_parsers.add_parser('add', allow_abbrev=False)
    add_parser.add_argument('tsv_path', metavar=('TSV_PATH'))

    add_parser.add_argument('--hide-uploads', default=False, action='store_true')
    add_parser.add_argument('--host', default=os.getenv('TQC_IP'))
    add_parser.add_argument('--port', default=os.getenv('TQC_PORT'))
    add_parser.add_argument('--api-key', default=os.getenv('TQC_ADD_KEY'))
    
    # Get request
    get_parser = request_parsers.add_parser('get', allow_abbrev=False, description='operators: lt, gt, leq, geq, eq, neq')
    get_parser.add_argument('--central-sample-id', default=None, nargs='+', action='append')
    get_parser.add_argument('--run-name', default=None, nargs='+', action='append')
    get_parser.add_argument('--pag-name', default=None, nargs='+', action='append')
    get_parser.add_argument('--pag-suppressed', default=None, nargs='+', action='append', help='Default: valid PAGs only')
    get_parser.add_argument('--pag-basic-qc', default=None, nargs='+', action='append', help='Default: passed PAGs only')
    get_parser.add_argument('--all', default=False, action='store_true', help='Ignore defaults regarding PAG suppression and basic QC passing')
    get_parser.add_argument('--sequencing-org-code', default=None, nargs='+', action='append')
    get_parser.add_argument('--foel-producer', default=None, nargs='+', action='append')
    get_parser.add_argument('--phe-private-provider', default=None, nargs='+', action='append')
    get_parser.add_argument('--phe-site', default=None, nargs='+', action='append')
    get_parser.add_argument('--collection-pillar', default=None, nargs='+', action='append')

    # Currently makes more sense to keep date filtering arguments for a given field separate from the same get request
    # As otherwise we would be doing an implicit mix of unions (between date arguments) and intersections (with every other argument) when matching rows
    # That could get confusing

    collection_date_parser = get_parser.add_mutually_exclusive_group()
    collection_date_parser.add_argument('--collection-date', default=None, nargs='+', metavar=('YYYY-MM-DD'), action='append')
    collection_date_parser.add_argument('--collection-date-range', default=None, nargs=2, metavar=('YYYY-MM-DD', 'YYYY-MM-DD'), action='append')
    collection_date_parser.add_argument('--collection-iso-week', default=None, nargs='+', metavar=('YYYY-WW'), action='append')
    collection_date_parser.add_argument('--collection-iso-week-range', default=None, nargs=2, metavar=('YYYY-WW', 'YYYY-WW'), action='append')

    received_date_parser = get_parser.add_mutually_exclusive_group()
    received_date_parser.add_argument('--received-date', default=None, nargs='+', metavar=('YYYY-MM-DD'), action='append')
    received_date_parser.add_argument('--received-date-range', default=None, nargs=2, metavar=('YYYY-MM-DD', 'YYYY-MM-DD'), action='append')
    received_date_parser.add_argument('--received-iso-week', default=None, nargs='+', metavar=('YYYY-WW'), action='append')
    received_date_parser.add_argument('--received-iso-week-range', default=None, nargs=2, metavar=('YYYY-WW', 'YYYY-WW'), action='append')

    sequencing_org_received_date_parser = get_parser.add_mutually_exclusive_group()
    sequencing_org_received_date_parser.add_argument('--sequencing-org-received-date', default=None, nargs='+', metavar=('YYYY-MM-DD'), action='append')
    sequencing_org_received_date_parser.add_argument('--sequencing-org-received-date-range', default=None, nargs=2, metavar=('YYYY-MM-DD', 'YYYY-MM-DD'), action='append')
    sequencing_org_received_date_parser.add_argument('--sequencing-org-received-iso-week', default=None, nargs='+', metavar=('YYYY-WW'), action='append')
    sequencing_org_received_date_parser.add_argument('--sequencing-org-received-iso-week-range', default=None, nargs=2, metavar=('YYYY-WW', 'YYYY-WW'), action='append')

    sequencing_submission_date_parser = get_parser.add_mutually_exclusive_group()
    sequencing_submission_date_parser.add_argument('--sequencing-submission-date', default=None, nargs='+', metavar=('YYYY-MM-DD'), action='append')
    sequencing_submission_date_parser.add_argument('--sequencing-submission-date-range', default=None, nargs=2, metavar=('YYYY-MM-DD', 'YYYY-MM-DD'), action='append')
    sequencing_submission_date_parser.add_argument('--sequencing-submission-iso-week', default=None, nargs='+', metavar=('YYYY-WW'), action='append')
    sequencing_submission_date_parser.add_argument('--sequencing-submission-iso-week-range', default=None, nargs=2, metavar=('YYYY-WW', 'YYYY-WW'), action='append')

    published_date_parser = get_parser.add_mutually_exclusive_group()
    published_date_parser.add_argument('--published-date', default=None, nargs='+', metavar=('YYYY-MM-DD'), action='append')
    published_date_parser.add_argument('--published-date-range', default=None, nargs=2, metavar=('YYYY-MM-DD', 'YYYY-MM-DD'), action='append')
    published_date_parser.add_argument('--published-iso-week', default=None, nargs='+', metavar=('YYYY-WW'), action='append')
    published_date_parser.add_argument('--published-iso-week-range', default=None, nargs=2, metavar=('YYYY-WW', 'YYYY-WW'), action='append')

    get_parser.add_argument('--fasta-path', default=None, nargs='+', action='append')
    get_parser.add_argument('--bam-path', default=None, nargs='+', action='append')
    get_parser.add_argument('--library-primers', default=None, nargs='+', action='append')
    get_parser.add_argument('--library-primers-reported', default=None, nargs='+', action='append')

    # FASTA QC
    get_parser.add_argument('--num-bases', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-acgt', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-masked', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-invalid', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-ambiguous', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--longest-gap', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--longest-ungap', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')

    # BAM QC
    get_parser.add_argument('--num-pos', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--mean-cov', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-pos-cov-gte1', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-pos-cov-gte5', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-pos-cov-gte10', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-pos-cov-gte20', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-pos-cov-gte50', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-pos-cov-gte100', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-pos-cov-gte200', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-tiles-medcov-gte1', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-tiles-medcov-gte5', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-tiles-medcov-gte10', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-tiles-medcov-gte20', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-tiles-medcov-gte50', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-tiles-medcov-gte100', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--pc-tiles-medcov-gte200', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')
    get_parser.add_argument('--tile-n', default=None, nargs=2, metavar=('OPERATOR', 'VALUE'), action='append')

    get_parser.add_argument('--metadata', default=None, metavar=('TSV_PATH'))

    get_parser.add_argument('--host', default=os.getenv('TQC_IP'))
    get_parser.add_argument('--port', default=os.getenv('TQC_PORT'))

    # Parse arguments
    args = parser.parse_args()

    url = f'http://{args.host}:{args.port}'

    if args.request_type == 'add':
        add(url, args.api_key, args.tsv_path, print_uploads=not args.hide_uploads)

    elif args.request_type == 'get':
        arguments = dict(args.__dict__)

        # Remove non-field related arguments
        arguments.pop('request_type')
        arguments.pop('metadata')
        arguments.pop('host')
        arguments.pop('port')
        arguments.pop('all')

        # Names of numeric TQC columns 
        numeric_args = numeric_columns()

        # Reject non-numeric arguments passed multiple times
        # Outer list for non-numeric arguments is then removed
        # This enables checks for multiple of the same --arg calls
        # Having them silently overwrite is not preferable and has been avoided
        for key, value in arguments.items(): 
            if not (key in numeric_args) and isinstance(value, list):
                if len(value) > 1:
                    raise Exception('Cannnot pass the same argument multiple times')
                arguments[key] = value[0]

        get(url, arguments, metadata_path=args.metadata, pag_defaults=not args.all)


if __name__ == '__main__':
    main()
