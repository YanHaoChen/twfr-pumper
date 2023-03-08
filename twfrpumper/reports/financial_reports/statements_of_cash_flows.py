from twfrpumper.reports.financial_reports.sheet import Sheet
from bs4 import BeautifulSoup


class StatementsOfCashFlows(Sheet):
    ID = 'StatementsOfCashFlows'

    def __init__(self, sheet: BeautifulSoup):
        self.magic_id = ''
        self.sheet = sheet
        self.dollar_unit = 0

    def magic_id(self):
        return 'StatementsOfCashFlows'