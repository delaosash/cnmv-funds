import logging
import os
import PyPDF2
import re
import sys
import tabula
import xlsxwriter
from funds_data import Security
from funds_data import FundInfo
from funds_data import Fund

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
STOCK_IDENTIFIER = 'acciones'

SAVE_TO_DB = False

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

def process_security(sec_desc, sec_info, fund_name, fund_percentage):
    stocks = 0.0
    bonds = 0.0
    isin_and_name = sec_desc.string.split(SECURITY_SEPARATOR)
    isin = isin_and_name[0].strip()
    type_and_name = isin_and_name[1].strip().split(TYPE_NAME_SEPARATOR)
    sec_type = type_and_name[0].lower()
    name = type_and_name[1]
    currency = sec_info[1].strip()
    try:
        value = int(sec_info[2].strip().replace('.', ''))
        percentage = float(sec_info[3].strip().replace(',', '.'))
        if percentage > 0.0:
            fund_info = FundInfo(name = fund_name, percentage = percentage, value = value)
            portfolio_percentage = percentage * fund_percentage     
            if isin in securities:
                security = securities[isin]
                security.percentage += portfolio_percentage
            else:
                security = Security(isin = isin, sec_type = sec_type, name = name, currency = currency, \
                    percentage = portfolio_percentage)
                securities[isin] = security
            security.add_fund(fund_info)
            if sec_type == STOCK_IDENTIFIER:
                stocks = percentage
            else:
                bonds = percentage
    except Exception as e:
        logging.warning('%s - %s not parsed, maybe an empty value. Error: %s', isin_and_name[0], isin_and_name[1], e)
    return stocks, bonds

def read_securities(securities, filename, fund_percentage):
    page_range_and_name = guess_securities_page_range_and_name(filename)
    str_range = str(page_range_and_name[0]) + PAGE_RANGE_SEPARATOR + str(page_range_and_name[1])
    fund_name = page_range_and_name[2]
    stocks = 0.0
    bonds = 0.0
    cash = 0.0
    dataframes = tabula.read_pdf(filename, pages=str_range)
    for df in dataframes:
        for item_value in df.values:
            parse_res = re.match(ISIN_REGEXP, str(item_value[0]))
            if parse_res:
                sec_percentage = process_security(parse_res, item_value, fund_name, fund_percentage)
                if sec_percentage[0] > 0:
                    stocks += sec_percentage[0]
                else:
                    bonds += sec_percentage[1]
    cash = 100 - stocks - bonds
    return fund_name, stocks, bonds, cash

def write_to_excel_and_db(securities):
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
        for j in range(len(securities[i].funds_info)):
            worksheet.write(i, 5 + j, securities[i].funds_info[j].name)
        if SAVE_TO_DB:
            securities[i].save()
    workbook.close()

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    if SAVE_TO_DB:
        Security.drop_collection()
        Fund.drop_collection()
    securities = dict()
    for item in sys.argv:
        idx = sys.argv.index(item)
        if idx % 2 != 0:
            filename = item
            fund_percentage = int(sys.argv[idx + 1]) / 100
            fund_name_and_assets = read_securities(securities, filename, fund_percentage)
            if SAVE_TO_DB:
                fund = Fund(name = fund_name_and_assets[0], percentage = fund_percentage * 100, \
                    stocks = fund_name_and_assets[1], bonds = fund_name_and_assets[2], cash = fund_name_and_assets[3])
                fund.save()
    securities_sorted_list = sorted(securities.values(), key = lambda s: s.percentage, reverse = True)
    total_percentage = 0.0
    for security in securities_sorted_list:
        total_percentage += security.percentage
        print(security)
    logging.info('Total: %d securities', len(securities))
    logging.info('Percentage invested: %f', total_percentage)
    liquidity = Security(isin=LIQUIDITY_ISIN, sec_type=LIQUIDITY_TYPE, name=LIQUIDITY_NAME, currency=LIQUIDITY_CURRENCY, \
        percentage=100 - total_percentage)
    securities_sorted_list.append(liquidity)
    write_to_excel_and_db(securities_sorted_list)
