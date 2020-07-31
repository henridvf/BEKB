from bs4 import BeautifulSoup
from requests import get

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException as WDE

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait

from lxml import html
from time import sleep
import argparse

import sys
import json
from re import sub
from datetime import datetime


def save_as_json(data):
    with open('data/output' + datetime.today().strftime('%d%m%y') + '.json', "w") as write_file:
        json.dump(data, write_file)


def parse_page(stmt):

    # with open("data/statement.html") as stmt:
    soup = BeautifulSoup(stmt, 'lxml')

    json_dict = {}

    try:
        # parse account info
        accts = soup.find('span', role='option')
        acct = accts.find('div', class_=lambda k: 'e3032e6a' in k)
        if not acct is None:
            # account_name = acct.contents[0].get_text()
            account_iban = acct.contents[1].get_text()
            account_curr = acct.contents[2].contents[0].get_text().strip()
            account_saldo = acct.contents[2].contents[1].get_text()

            json_dict = {
                'bankid': '00000790',   # BC (Bank Clearing) number BEKB
                'acctid': str.replace(account_iban, ' ', ''),
                'curdef': account_curr,
                'balamt': sub(r'[^\d\-.]', '', account_saldo)
            }

        # parse transactions
        trans_lst = []
        for i in soup.find_all('div', role='rowgroup'):

            trans_dict = {}
            date = i.find_all('div', lambda x: 'pdf-wrap DataGridCell' in x)
            trans_type = i.find_all('div', title='[object Object]')
            payee = i.find('span', class_='bold')
            amount = i.find_all('div', lambda y: 'CurrencyRenderer' in y)

            dte = datetime.strptime(date[0].get_text(), '%d.%m.%Y')

            if not payee is None:
                trans_type_ext = str(trans_type[0].text)[:-len(payee.text)]
                name = payee.text
                trntype = trans_type_ext
            else:
                name = 'NONREF'
                trntype = trans_type[0].text

            # for json
            trans_dict = {
                'dtposted': datetime.strftime(dte, '%Y%m%d'),
                'trntype': trntype,
                'trnamt': sub(r'[^\d\-.]', '', amount[0].text),
                'name': name}

            trans_lst.append(trans_dict.copy())

        # add transactions to json dict
        json_dict['transactions'] = trans_lst

        # save
        save_as_json(json_dict)

    except Exception as error:
        print(error)


def get_transactions():
    html = None
    url_statement = 'https://banking.bekb.ch/portal/?bank=5&path=layout/bekb&lang=de#/transactions'
    url = 'https://banking.bekb.ch/portal/?bank=5&path=layout/bekb&lang=de#/main?redirect=/'

    browser = webdriver.Safari()
    browser.get(url)

    try:
        # simulate submit on login
        browser.find_element_by_name('vertrag').submit()

        # small delay is crucial to allow time for 2-way authentication via app
        wait(browser, 20).until(EC.url_contains('cockpit'))

        browser.get(url_statement)
        # wait(browser, 15).until(EC.url_contains('transactions'))

        # waiting for table with transactions to load; alternatively use sleep(10)
        wait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'rt-table')))
        html = browser.page_source

    except WDE:
        print('Cannot find element')
    finally:
        browser.quit()

    return html


# Main
def main():
    statement = get_transactions()
    parse_page(statement)

    print('Complete!')

# Currently used as module for ofx.py, but can be used as standalone script
if __name__ == '__main__':
    # Define the program description
    text = 'This program parses an HTML bank file (BEKB) to an OFX file.'
    usage = 'python extract.py'

    # Initiate the parser with a description
    parser = argparse.ArgumentParser(description=text, usage=usage)
    parser.add_argument("-V", "--version",
                        help="show program version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print("version 0.1")

    # Run function
    main()
