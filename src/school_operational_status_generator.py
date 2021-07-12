# -*- coding: utf-8 -*-
""" Purpose:  Generates data file templates for reporting school operational status.
 Reads a CSV file containing school, LEA, and State identifying information.
 Generates a JSON data file for each State, listing the LEAs and schools within the State, in a format compliant with a JSON schema.
 
 Author: odp@ed.gov
 
 Usage::
     
     python school_open_status_generator.py ccdfile.csv [--outputdir=dirpath] [--conformance=URL] [--schema=URL]
     
"""

from __future__ import print_function

import argparse
import json
import logging
import os
import pathlib
import sys

import pandas

# Set the default level of detail for log messages.
logger = logging.getLogger(__name__)
LOG_LEVEL = 'INFO'

CCD_FILE = "ccd_sch_sas.csv"

#Set constants that every JSON output file should contain.
CONFORMANCE_URL = 'https://data.ed.gov/v1.0/schema/schooloperationalstatus'
SCHEMA_URL = 'https://data.ed.gov/v1.0/schema/schooloperationalstatus.schema.json'

# Default the output directory to the current directory.
OUTPUT_DIR = '.'

#Set some constants for formatting the output.
PREFIX_FORMAT = """{
"conformsTo": "%s",
"describedBy": "%s",
"reportingPeriodStartDate": "2021-05-10",
"comment": "For each school, record All if all enrolled students were offered in-person instruction the full week",
"comment": "record None if no enrolled student was offered in-person instruction any day of the reporting week,",
"comment": "record Hybrid if the school was in session but the other two responses are not accurate,",
"comment": "and record Not in session if the school was not in session for the reporting week.",
"lea": [
"""

LEA_PREFIX_FORMAT = """{"leaID": "%s", "leaName": "%s", "openStatus": [
"""

LEA_SUFFIX = """
]}"""
    
SCHOOL_FORMAT = """  { "weeklyInPersonInstruction": "Not reported", "schoolID": "%s", "schoolName": "%s" }"""

SEPARATOR = ",\n"

SUFFIX = """
]
}
"""

defaults = { 'ccd_file': CCD_FILE, 'output_dir': OUTPUT_DIR, 'conforms_to': CONFORMANCE_URL, 'described_by': SCHEMA_URL, 'log_level': LOG_LEVEL}

def main(args):
    
    # Set up logging to use a common format and send log messages to standard output.
    logging.basicConfig(stream=sys.stdout, level=getattr(logging, args.log_level),
                        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d %(funcName)s()] %(message)s')
    
    # Read the file in as a CSV
    sidf = pandas.read_csv(args.ccd_file, usecols=['ST','LEAID','LEA_NAME','NCESSCH','SCH_NAME'], index_col=['ST','LEAID','NCESSCH'])
    
    #Write out JSON files for each State separately.
    for state, lea_grp in sidf.groupby(level='ST'):
        # Create a directory named after the State.
        opath = args.output_dir / state
        opath.mkdir(exist_ok=True)
        
        jtf = opath / 'school_operational_status.json'
        
        # Write the JSON content manually, to add other elements and control formatting.
        with jtf.open(mode='w') as j:
            print( PREFIX_FORMAT % (args.conforms_to, args.described_by), file=j)
            # Iterate over the LEAs within the state in a while loop, so the JSON
            # separator between entries can be inserted on all but the last LEA
            lea_iter = iter(lea_grp.groupby(level='LEAID'))
            lea, sch_grp = next(lea_iter)
            print(LEA_PREFIX_FORMAT %(lea, sch_grp.iloc[0]['LEA_NAME']), end='',file=j)
            # Iterate over all the schools within the first LEA.
            schi = 0
            print(SCHOOL_FORMAT %(sch_grp.index.values[schi][2], sch_grp.iloc[schi]['SCH_NAME']), end='', file=j)
            schi += 1
            while schi < len(sch_grp.index):
                print(SEPARATOR, end='', file=j)
                print(SCHOOL_FORMAT %(sch_grp.index.values[schi][2], sch_grp.iloc[schi]['SCH_NAME']), end='', file=j)
                schi += 1
            print(LEA_SUFFIX, end='', file=j)
            # Iterate over the remaining LEAs in the state
            while True:
                try:
                    lea,sch_grp = next(lea_iter)
                    print(SEPARATOR, end='',file=j)
                    print(LEA_PREFIX_FORMAT %(lea, sch_grp.iloc[0]['LEA_NAME']), end='',file=j)
                    # Iterate over all the schools within the LEA.
                    schi = 0
                    print(SCHOOL_FORMAT %(sch_grp.index.values[schi][2], sch_grp.iloc[schi]['SCH_NAME']), end='', file=j)
                    schi += 1
                    while schi < len(sch_grp.index):
                        print(SEPARATOR, end='',file=j)
                        print(SCHOOL_FORMAT %(sch_grp.index.values[schi][2], sch_grp.iloc[schi]['SCH_NAME']), end='', file=j)
                        schi += 1
                    print(LEA_SUFFIX, end='',file=j)
                except StopIteration:
                    break
            print(SUFFIX, file=j)
    
        
# Check environment variables to see if there are overrides for the hardcoded defaults.    
defaults['ccd_file'] = os.getenv('SOS_CCDFILE',default=defaults['ccd_file'])
defaults['output_dir'] = pathlib.Path(os.getenv('SOS_OUTPUTDIR', default=defaults['output_dir']))
defaults['conforms_to'] = os.getenv('SOS_CONFORMANCE', default=defaults['conforms_to'])
defaults['described_by'] = os.getenv('SOS_SCHEMA', default=defaults['described_by'])
defaults['log_level'] = os.getenv('SOS_LOGLEVEL', default=defaults['log_level'])
    
# Process command line arguments for final parameters.
parser = argparse.ArgumentParser(description = 'Generate JSON templates for aggregating school operational status.')
parser.add_argument('--ccdfile', dest='ccd_file', default = defaults['ccd_file'], help='Name of the Common Core Data file containing school identifying information to include in the template files.')
parser.add_argument('--outputdir', dest='output_dir', default= defaults['output_dir'], help='Directory path where template files will be wrwitten.', type=pathlib.Path)
parser.add_argument('--conformance', dest='conforms_to', default = defaults['conforms_to'], help='URL to embed in a conformsTo element.')
parser.add_argument('--schema', dest='described_by', default= defaults['described_by'], help='URL to embed for the reference JSON schema.')
parser.add_argument('--loglevel', dest = 'log_level', default=defaults['log_level'], choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'])
    
args = parser.parse_args()
    
#Call the main function
main(args)