import requests
import logging

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
            report_type: str
    ):
        try:
            resp = requests.get(
                f'https://mops.twse.com.tw/server-java/t164sb01?step=1&'
                f'CO_ID={company_id}&'
                f'SYEAR={year}&'
                f'SSEASON={season}&'
                f'REPORT_ID={report_type}')
            resp.encoding = 'big5'
            soup = BeautifulSoup(resp.text, 'html.parser')

            check_status = soup.find('h4')
            if check_status and check_status.string == '檔案不存在!':
                return None
            else:
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
