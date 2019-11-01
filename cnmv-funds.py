import logging
import os
import PyPDF2
import re
import sys
import tabula
import xlsxwriter

TEXT_TO_FIND = 'Detalle de inversiones financieras'
FUND_NAME_DELIMITER = 'Nº Registro CNMV'
UNKNOWN_FUND_NAME = 'unknown'
ISIN_REGEXP = r'\b([A-Z]{2})((?![A-Z]{10}\b)[A-Z0-9]{10})\b'
PAGE_RANGE_SEPARATOR = '-'
SECURITY_SEPARATOR = '-'
TYPE_NAME_SEPARATOR = '|'
EXCEL_FILENAME = 'portfolio.xlsx'
LIQUIDITY_ISIN = 'ES0000000000'
LIQUIDITY_TYPE = 'liquidez'
LIQUIDITY_NAME = 'Liquidez'
LIQUIDITY_CURRENCY = 'EUR'

class FundInfo():
    def __init__(self, name, percentage, value):
        self.name = name
        self.percentage = percentage
        self.value = value
    def __str__(self):
        return self.name + '; ' + str(self.percentage) + '; ' + str(self.value)

class Security():
    def __init__(self, isin, sec_type, name, currency, percentage):
        self.isin = isin
        self.sec_type = sec_type
        self.name = name
        self.currency = currency
        self.percentage = percentage
        self.funds = []
    def add_fund(self, fund_info):
        self.funds.append(fund_info)
    def __str__(self):
        ret_str = self.isin + ' - ' + self.sec_type + ' - ' + self.name + ' - ' + self.currency  + ' - ' + str(self.percentage)
        if (len(self.funds) > 0):
            ret_str += ' ### funds: '
            for fund_info in self.funds:
                ret_str += str(fund_info) + ' ## '
        return ret_str

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

def read_securities(securities, filename, fund_percentage):
    page_range_and_name = guess_securities_page_range_and_name(filename)
    str_range = str(page_range_and_name[0]) + PAGE_RANGE_SEPARATOR + str(page_range_and_name[1])
    fund_name = page_range_and_name[2]
    df = tabula.read_pdf(filename, pages=str_range)
    for item_value in df.values:
        parse_res = re.match(ISIN_REGEXP, str(item_value[0]))
        if parse_res:
            isin_and_name = parse_res.string.split(SECURITY_SEPARATOR)
            isin = isin_and_name[0].strip()
            type_and_name = isin_and_name[1].strip().split(TYPE_NAME_SEPARATOR)
            sec_type = type_and_name[0].lower()
            name = type_and_name[1]
            currency = item_value[1].strip()
            try:
                value = int(item_value[2].strip().replace('.', ''))
                percentage = float(item_value[3].strip().replace(',', '.'))
                if percentage > 0.0:
                    security_fund_info = FundInfo(fund_name, percentage, value)
                    portfolio_percentage = percentage * fund_percentage     
                    if isin in securities:
                        security = securities[isin]
                        security.percentage += portfolio_percentage
                    else:
                        security = Security(isin, sec_type, name, currency, portfolio_percentage)
                        securities[isin] = security
                    security.add_fund(security_fund_info)
            except Exception:
                logging.warning('%s - %s not parsed, maybe an empty value', isin_and_name[0], isin_and_name[1])

def write_to_excel(securities):
    workbook = xlsxwriter.Workbook(EXCEL_FILENAME)
    worksheet = workbook.add_worksheet()
    worksheet.set_column('A:A', 20)
    worksheet.set_column('C:C', 30)
    worksheet.set_column('F:H', 30)
    for i in range(len(securities)):
        worksheet.write(i, 0, securities[i].isin)
        worksheet.write(i, 1, securities[i].sec_type)
        worksheet.write(i, 2, securities[i].name)
        worksheet.write(i, 3, securities[i].currency)
        worksheet.write(i, 4, securities[i].percentage)
        for j in range(len(securities[i].funds)):
            worksheet.write(i, 5 + j, securities[i].funds[j].name)
    workbook.close()

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    securities = dict()
    for item in sys.argv:
        idx = sys.argv.index(item)
        if idx % 2 != 0:
            filename = item
            fund_percentage = int(sys.argv[idx + 1]) / 100
            read_securities(securities, filename, fund_percentage)
    securities_sorted_list = sorted(securities.values(), key = lambda s: s.percentage, reverse = True)
    total_percentage = 0.0
    for security in securities_sorted_list:
        total_percentage += security.percentage
        print(security)
    logging.info('Total: %d securities', len(securities))
    logging.info('Percentage invested: %f', total_percentage)
    liquidity = Security(LIQUIDITY_ISIN, LIQUIDITY_TYPE, LIQUIDITY_NAME, LIQUIDITY_CURRENCY, 100 - total_percentage)
    securities_sorted_list.append(liquidity)
    write_to_excel(securities_sorted_list)
