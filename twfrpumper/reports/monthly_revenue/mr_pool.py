from dataclasses import dataclass, asdict
from os import makedirs, path
import logging

import pandas as pd
import plotly.express as px

from twfrpumper.reports.monthly_revenue.monthly_revenue_agent import MonthlyRevenueAgent
from twfrpumper.reports.monthly_revenue.monthly_revenue_agent import MonthlyRevenueReport
from twfrpumper.reports.monthly_revenue.monthly_revenue_agent import MarketType


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
    def __init__(self):
        self.__agent = MonthlyRevenueAgent()
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
            self.report_df = self.report_df.append(list_r[i].report_df, ignore_index=True)


if __name__ == "__main__":
    mr_pool = MRPool()
    mr_pool.add_range_reports(2023, 1, 2023, 3)
    mr_pool.organize_reports()
