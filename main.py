from twfr_pumper.reports.financial_reports.financial_report_agent import FinancialReportAgent
from bs4 import BeautifulSoup


def print_hi():
    fn_report_agent = FinancialReportAgent("2605", 2020, 3, "C")
    # print(fn_report_agent.balance_sheet.sheet)
    print(fn_report_agent.balance_sheet.dict_format)
    print(fn_report_agent.comprehensive_income_sheet.dict_format)


if __name__ == '__main__':
    print_hi()
