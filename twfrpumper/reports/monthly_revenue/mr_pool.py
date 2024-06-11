from dataclasses import dataclass

import pandas as pd
import plotly.express as px

from twfrpumper.reports.monthly_revenue.monthly_revenue_agent import MonthlyRevenueAgent
from twfrpumper.reports.monthly_revenue.monthly_revenue_agent import MonthlyRevenueReport
from twfrpumper.reports.monthly_revenue.monthly_revenue_agent import MarketType

ITEM_ZH_MAPPING = {
    'operating_revenue': '營業收入-當月營收',
    'or_prev_mon': '營業收入-上月營收',
    'or_prev_year': '營業收入-去年當月營收',
    'or_vs_pm': '營業收入-上月比較增減(%)',
    'or_vs_py': '營業收入-去年同月增減(%)',
    'acc_or': '累計營業收入-當月累計營收',
    'acc_or_prev_year': '累計營業收入-去年累計營收',
    'acc_or_vs_prev_year': '累計營業收入-前期比較增減(%)'}


@dataclass
class DFRecord:
    code: str
    company_name: str
    y_and_m: str
    item: str
    zh: str
    en: str
    value: float = 0.0


class MRPool(object):
    def __init__(self, delay_initial, delay_max):
        self.__agent = MonthlyRevenueAgent(delay_initial=delay_initial, delay_max=delay_max)
        self.reports = set()
        self.organized_report = {}
        self.report_df = None
        self.name_mapping = {}

    def add_report(self, report: MonthlyRevenueReport):
        if report:
            self.reports.add(report)

    def add_range_reports(self, start_y: int, start_m: int, end_y: int, end_m: int,
                          market_type: MarketType = MarketType.LISTED_STOCK):
        start_y_m = start_y * 100 + start_m
        end_y_m = end_y * 100 + end_m
        while start_y_m <= end_y_m:
            self.add_report(self.__agent.get_report(start_y, start_m, market_type))
            start_m += 1
            if start_m == 13:
                start_m = 1
                start_y += 1
            start_y_m = start_y * 100 + start_m

    def organize_reports(self):
        list_r = list(self.reports)
        if not list_r:
            return None
        self.report_df = list_r[0].report_df
        for i in range(1, len(list_r)):
            self.report_df = pd.concat([self.report_df, list_r[i].report_df], ignore_index=True)


    def draw(self, item, company_codes, title_lang=True):
        title = item
        if title_lang:
            title = ITEM_ZH_MAPPING[item]

        item_df = self.report_df[self.report_df.code.isin(company_codes)].sort_values(by=['y_and_m'])

        fig = px.line(item_df,
                      x='y_and_m',
                      y=item,
                      color='company_name',
                      title=title)
        fig.show()


if __name__ == "__main__":
    mr_pool = MRPool(5,10)
    mr_pool.add_range_reports(2019, 1, 2019, 12)
    mr_pool.organize_reports()
