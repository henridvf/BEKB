from datetime import datetime
from datetime import timezone
from decimal import Decimal

import xml.etree.ElementTree as ET 

import xml.dom.minidom as md
import argparse
import json

import extract


def statement_date_range(statement):
    ''' Identifies the start and end dates of statement transactions list.
        Currently simply compares integers instead of dates
    '''
    dates = []
    sd = statement
    for tr in sd['transactions']:
        dates.append(tr.get('dtposted'))

    return min(dates), max(dates)


def ofx_body(statement):
    ''' Construction of the OFX body

        input(s): JSON statement
        output(s): utf-8 decoded ofx body
    '''
    
    # create abbreviation
    sd = statement

    # Build OFX
    root = ET.Element('OFX')

    signonmsgsrsv1 = ET.SubElement(root, 'SIGNONMSGSRSV1')
    sonrs = ET.SubElement(signonmsgsrsv1, 'SONRS')
    status = ET.SubElement(sonrs, 'STATUS')
    ET.SubElement(status, 'CODE').text = '0'
    ET.SubElement(status, 'SEVERITY').text = 'INFO'
    ET.SubElement(sonrs, 'DTSERVER').text =  datetime.strftime(datetime.now(), '%Y%m%d')
    ET.SubElement(sonrs, 'LANGUAGE').text = 'ENG'

    bankmsgsrsv1 = ET.SubElement(root, 'BANKMSGSRSV1')
    stmttrnrs = ET.SubElement(bankmsgsrsv1, 'STMTTRNRS')
    ET.SubElement(stmttrnrs, 'TRNUID').text = '00001'
    status = ET.SubElement(stmttrnrs, 'STATUS')
    ET.SubElement(status, 'CODE').text = '0'
    ET.SubElement(status, 'SEVERITY').text = 'INFO'

    stmtrs = ET.SubElement(stmttrnrs, 'STMTRS')
    ET.SubElement(stmtrs, 'CURDEF').text = sd['curdef']
    bankacctfrom = ET.SubElement(stmtrs, 'BANKACCTFROM')
    ET.SubElement(bankacctfrom, 'BANKID').text = sd['bankid']
    ET.SubElement(bankacctfrom, 'ACCTID').text = sd['acctid']
    ET.SubElement(bankacctfrom, 'ACCTTYPE').text = 'CHECKING'
    
    dtstart, dtend = statement_date_range(sd)

    banktranlist = ET.SubElement(stmtrs, 'BANKTRANLIST')
    ET.SubElement(banktranlist, 'DTSTART').text = dtstart
    ET.SubElement(banktranlist, 'DTEND').text = dtend

    trntypes = {'Ihr E-Banking-Auftrag': 'DEBIT',
                'Ihr Dauerauftrag': 'DEBIT',
                'Ihr LSV-Auftrag': 'DEBIT',
                'Ihr Zahlungsauftrag': 'DEBIT',
                'Hypotheken/Darlehen Verrechnung': 'DEBIT',
                'Monatsgebühr': 'DEBIT',
                'Uebertrag': 'DEBIT',
                'Abschlussbetreffnis': 'DEBIT',
                'Zahlungseingang': 'CREDIT',
                'Einzahlung': 'CREDIT'}
    
    i = 0
    for tr in sd['transactions']:
        
        i += 1
        stmttrn = ET.SubElement(banktranlist, 'STMTTRN')
        ET.SubElement(stmttrn, 'TRNTYPE').text = trntypes.get(tr.get('trntype'))
        ET.SubElement(stmttrn, 'DTPOSTED').text = tr.get('dtposted')
        ET.SubElement(stmttrn, 'TRNAMT').text = str(tr.get('trnamt'))
        ET.SubElement(stmttrn, 'FITID').text = str(i).zfill(5)
        ET.SubElement(stmttrn, 'NAME').text = tr.get('name')[:32]
        ET.SubElement(stmttrn, 'MEMO').text = tr.get('trntype')

    ledgerbal = ET.SubElement(stmtrs, 'LEDGERBAL')
    ET.SubElement(ledgerbal, 'BALAMT').text = sd['balamt']
    ET.SubElement(ledgerbal, 'DTASOF').text = datetime.strftime(datetime.now(), '%Y%m%d')
   
    body = ET.tostring(root, encoding='utf-8').decode('utf-8')
    
    return body


def ofx_header(version=102):
    ''' Creates the OFX header. It is more or less static from experience.
    '''

    # This string needs to be strangely left aligned within the def to work properly
    header = '''OFXHEADER:100
DATA:OFXSGML
VERSION:''' + str(version) + '''
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

'''
    return header


def build_ofx(statement, debug=False):
    body = ofx_body(statement)
    header = ofx_header()
    
    # for easier xml debugging, using formatted xml
    if debug:
        xml = md.parseString(body)
        body = xml.toprettyxml()

    response = header + body

    with open('data/output' + datetime.today().strftime('%d%m%y') + '.ofx', 'w') as text_file:
        text_file.write(response)


def main():

    # run extract
    statement = extract.get_transactions()
    extract.parse_page(statement)

    # get json file and parse into ofx
    with open('data/output' + datetime.today().strftime('%d%m%y') + '.json') as file_object:
        data = json.load(file_object)
        build_ofx(data)

# Main
if __name__ == '__main__':
    # Define the program description
    text = 'This program scrapes BEKB bankstatement and converts JSON file to an OFX file.'
    usage = 'python ofx.py'

    # Initiate the parser with a description
    parser = argparse.ArgumentParser(description=text, usage=usage)
    parser.add_argument("-V", "--version", help="show program version", action="store_true")
    # parser.add_argument("-f", "--file", help="input file")
    args = parser.parse_args()

    if args.version:
        print("version 0.1")

    # Run function
    main()
