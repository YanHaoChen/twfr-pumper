import requests
import logging
from os.path import exists, isdir, join
from os import mkdir
from bs4 import BeautifulSoup

from twfr_pumper.reports.financial_reports.sheet import Sheet
from twfr_pumper.reports.financial_reports.balance_sheet import BalanceSheet
from twfr_pumper.reports.financial_reports.comprehensive_income_sheet import ComprehensiveIncomeSheet


class FinancialReportAgent(object):
    def __new__(
            cls,
            company_id: str,
            year: int,
            season: int,
            report_type: str,
            file_path="./tmp/"
    ):
        content = None
        try:
            if not (exists(file_path) and isdir(file_path)):
                mkdir(file_path)

            report_file_name = join(file_path, f'{company_id}_{report_type}_{year}_{season}.html')
            if exists(report_file_name):
                with open(report_file_name, 'r', encoding='big5') as f:
                    content = f.read()
            else:
                resp = requests.get(
                    f'https://mops.twse.com.tw/server-java/t164sb01?step=1&'
                    f'CO_ID={company_id}&'
                    f'SYEAR={year}&'
                    f'SSEASON={season}&'
                    f'REPORT_ID={report_type}')
                resp.encoding = 'big5'
                content = resp.text

            soup = BeautifulSoup(content, 'html.parser')
            check_status = soup.find('h4')
            if check_status and check_status.string == '檔案不存在!':
                return None
            else:
                with open(report_file_name, 'w', encoding='big5') as f:
                    f.write(content)
                instance = super(FinancialReportAgent, cls).__new__(cls)
                instance.__dict__['soup'] = soup
                return instance
        except Exception as e:
            logging.exception(e)

    def __init__(
            self,
            company_id: str,
            year: int,
            season: int,
            report_type: str,
    ):
        self.company_id = company_id
        self.year = year
        self.season = season
        self.report_type = report_type
        self.tables = self.soup.find_all('table')
        self.balance_sheet = BalanceSheet(self.tables[0])
        self.parse_sheet_unit(self.balance_sheet, self.soup)
        self.comprehensive_income_sheet = ComprehensiveIncomeSheet(self.tables[1])
        self.parse_sheet_unit(self.comprehensive_income_sheet, self.soup)

    @staticmethod
    def parse_sheet_unit(sheet: Sheet, report_html: BeautifulSoup):
        unit_string = report_html.find(
            'div', id=sheet.magic_id
        ).find_next(
            'div', 'rptidx'
        ).find(
            'span', 'en'
        ).string

        if 'thousands' in unit_string:
            sheet.set_dollar_unit(1000)
        else:
            logging.warning(f'Unknown unit: {unit_string}')

        return sheet
