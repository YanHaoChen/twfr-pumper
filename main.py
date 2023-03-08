import pandas as pd

from twfrpumper.reports.financial_reports.financial_report_agent import FinancialReportAgent
from twfrpumper.reports.financial_reports.fr_pool import FRPool


def try_run():
    fn_report_agent = FinancialReportAgent("2605", 2020, 3, "C")
    print(fn_report_agent.balance_sheet.dict_format)
    print(fn_report_agent.comprehensive_income_sheet.dict_format)

    pool = FRPool()
    pool.add_range_reports("1227", "C", 2020, 1, 2022, 3)
    pool.organize_reports()
    pool.draw('s_roa')
    pool.draw('8200')


if __name__ == '__main__':
    try_run()
