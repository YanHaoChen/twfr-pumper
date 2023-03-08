import requests
import logging
from os.path import exists, isdir, join
from os import makedirs
import time
import random

from bs4 import BeautifulSoup

from twfrpumper.reports.financial_reports.sheet import Sheet
from twfrpumper.reports.financial_reports.balance_sheet import BalanceSheet
from twfrpumper.reports.financial_reports.comprehensive_income_sheet import ComprehensiveIncomeSheet
from twfrpumper.reports.financial_reports.statements_of_cash_flows import StatementsOfCashFlows


class FinancialReport(object):
    def __init__(self,
                 stock_id: str,
                 company_name: str,
                 year: int,
                 season: int,
                 report_type: str,
                 balance_sheet: BalanceSheet,
                 ci_sheet: ComprehensiveIncomeSheet,
                 cash_flows: StatementsOfCashFlows,
                 soup: BeautifulSoup):
        self.stock_id = stock_id
        self.company_name = company_name
        self.year = year
        self.season = season
        self.report_type = report_type
        self.balance_sheet = balance_sheet
        self.ci_sheet = ci_sheet
        self.cash_flows = cash_flows
        self.soup = soup

    def __hash__(self):
        return hash(f'{self.stock_id}{self.year}{self.season}{self.report_type}')

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class FinancialReportAgent(object):
    def __init__(self, delay_initial=1, delay_max=3, file_folder="./tmp/"):
        self.delay_initial = delay_initial
        self.delay_max = delay_max
        self.file_folder = file_folder

        if not (exists(self.file_folder) and isdir(self.file_folder)):
            makedirs(self.file_folder, exist_ok=True)

    def get_report(self, stock_id: str, year: int, season: int, report_type: str):
        report_file_name = join(self.file_folder, f'{stock_id}_{report_type}_{year}_{season}.html')
        if exists(report_file_name):
            with open(report_file_name, 'r', encoding='big5') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                company_name_dom = soup.find('ix:nonnumeric').find_next_sibling('ix:nonnumeric')
        else:
            resp = requests.get(
                f'https://mops.twse.com.tw/server-java/t164sb01?step=1&'
                f'CO_ID={stock_id}&'
                f'SYEAR={year}&'
                f'SSEASON={season}&'
                f'REPORT_ID={report_type}')
            resp.encoding = 'big5'
            content = resp.text
            time.sleep(random.randint(self.delay_initial, self.delay_max))
            soup = BeautifulSoup(content, 'html.parser')
            company_name_dom = soup.find('ix:nonnumeric').find_next_sibling('ix:nonnumeric')

            if company_name_dom:
                with open(report_file_name, 'w', encoding='big5') as f:
                    f.write(content)
            else:
                logging.warning(f"Can't get the report: {report_file_name}")
                return None

        balance_table = soup.find('table')
        balance_sheet = BalanceSheet(balance_table)
        self.parse_sheet_unit(balance_sheet, soup)
        ci_table = balance_table.find_next_sibling('table')
        ci_sheet = ComprehensiveIncomeSheet(ci_table)
        self.parse_sheet_unit(ci_sheet, soup)
        cash_flows = StatementsOfCashFlows(ci_table.find_next_sibling('table'))
        self.parse_sheet_unit(cash_flows, soup)

        return FinancialReport(
            stock_id=stock_id,
            company_name=company_name_dom.text,
            year=year,
            season=season,
            report_type=report_type,
            balance_sheet=balance_sheet,
            ci_sheet=ci_sheet,
            cash_flows=cash_flows,
            soup=soup
        )

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


if __name__ == "__main__":
    agent = FinancialReportAgent()
    report = agent.get_report("2330", 2022, 3, "C")