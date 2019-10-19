import logging
import os
import PyPDF2
import re
import sys
import tabula

TEXT_TO_FIND = 'Detalle de inversiones financieras'
FUND_NAME_DELIMITER = 'Nº Registro CNMV'
UNKNOWN_FUND_NAME = 'unknown'
ISIN_REGEXP = r'\b([A-Z]{2})((?![A-Z]{10}\b)[A-Z0-9]{10})\b'
PAGE_RANGE_SEPARATOR = '-'
SECURITY_SEPARATOR = '-'

class Security():
    def __init__(self, isin, name, currency, value, percentage):
        self.isin = isin
        self.name = name
        self.currency = currency
        self.value = value
        self.percentage = percentage
    def __str__(self):
        return self.isin + ' - ' + self.name + ' - ' + self.currency  + ' - ' + str(self.value)  + ' - ' + str(self.percentage)

def guess_securities_page_range_and_name(filename):
    pdf_file = open(filename, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file, strict=False)
    page_obj = pdf_reader.getPage(0)
    text = page_obj.extractText()
    position = text.find(FUND_NAME_DELIMITER)
    if position == -1:
        fund_name = UNKNOWN_FUND_NAME
    else:
        fund_name = text[2:position]
    page = pdf_reader.numPages - 1
    found = False
    while not found:
        page_obj = pdf_reader.getPage(page)
        text = page_obj.extractText()
        if text.find(TEXT_TO_FIND) != -1:
            found = True
        else:
            page -= 1
    return page + 1, pdf_reader.numPages, fund_name

def read_securities():
    filename = sys.argv[1] 
    page_range_and_name = guess_securities_page_range_and_name(filename)
    str_range = str(page_range_and_name[0]) + PAGE_RANGE_SEPARATOR + str(page_range_and_name[1])
    fund_name = page_range_and_name[2]
    df = tabula.read_pdf(filename, pages=str_range)
    securities = dict()
    for item_value in df.values:
        parse_res = re.match(ISIN_REGEXP, str(item_value[0]))
        if parse_res:
            isin_and_name = parse_res.string.split(SECURITY_SEPARATOR)
            isin = isin_and_name[0].strip()
            name = isin_and_name[1].strip()
            currency = item_value[1].strip()
            try:
                value = int(item_value[2].strip().replace('.', ''))
                percentage = float(item_value[3].strip().replace(',', '.'))
                security = Security(isin, name, currency, value, percentage)
                securities[isin] = security
            except Exception:
                logging.warning('%s not parsed, maybe an empty value', isin)
    return securities

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    securities = read_securities()
    for security in securities.values():
        print(security)
    logging.info('Total: %d securities', len(securities))


