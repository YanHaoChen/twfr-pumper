import requests
import io
from os.path import exists, isdir, join
from os import makedirs
from datetime import date
from enum import Enum
from typing import Union
import time
import random

import pandas as pd

from twfrpumper.toolbox.date_tool import DateTool


class MarketType(Enum):
    LISTED_STOCK = 0
    OTC_MARKET = 1


class MonthlyRevenueReport(object):
    def __init__(self, year, month, report_df, market: MarketType):
        self.year = year
        self.month = month
        self.str_y_and_m = f'{year * 100 + month}'
        self.report_df = report_df
        self.market = market
        self.__add_new_cols()

    def __add_new_cols(self):
        self.report_df = self.report_df.assign(y_and_m=self.str_y_and_m)
        self.report_df = self.report_df.assign(market_type=self.market)
        self.report_df["company_name"] = self.report_df['公司代號'].astype(str) + "-" + self.report_df['公司名稱']
        self.report_df.rename(columns={
            '公司代號': 'code',
            '公司名稱': 'name',
            '營業收入-當月營收': 'operating_revenue',
            '營業收入-上月營收': 'or_prev_mon',
            '營業收入-去年當月營收': 'or_prev_year',
            '營業收入-上月比較增減(%)': 'or_vs_pm',
            '營業收入-去年同月增減(%)': 'or_vs_py',
            '累計營業收入-當月累計營收': 'acc_or',
            '累計營業收入-去年累計營收': 'acc_or_prev_year',
            '累計營業收入-前期比較增減(%)': 'acc_or_vs_prev_year'}, inplace=True)

    def get_industry_list(self):
        return self.report_df['產業別'].unique().tolist()

    def get_company_name_list(self):
        return self.report_df['公司名稱'].unique().tolist()

    def get_company_list_by_industry(self, industry: str):
        return self.report_df.loc[self.report_df['產業別'] == industry][['公司代號', '公司名稱']].values.tolist()

    def get_company_df_by_industry(self, industry: str):
        return self.report_df.loc[self.report_df['產業別'] == industry]

    def check_industry_by_code(self, code: Union[int, str]) -> Union[str, None]:
        if isinstance(code, str):
            code = int(code)
        try:
            return self.report_df.loc[self.report_df['公司代號'] == code]['產業別'].values[0]
        except IndexError:
            return None

    def check_industry_by_name(self, name: str) -> Union[str, None]:
        try:
            return self.report_df.loc[self.report_df['公司名稱'] == name]['產業別'].values[0]
        except IndexError:
            return None

    def __hash__(self):
        return hash(f'{self.year}{self.month}{self.market}')

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class MonthlyRevenueAgent(object):
    FILE_PATH_MAPPING = {
        MarketType.LISTED_STOCK: '/t21/sii/',
        MarketType.OTC_MARKET: '/t21/otc/'
    }

    def __init__(self, delay_initial=1, delay_max=3, file_folder="./tmp/monthly_revenue"):
        self.delay_initial = delay_initial
        self.delay_max = delay_max
        self.file_folder = file_folder
        self.today = date.today()
        if not (exists(self.file_folder) and isdir(self.file_folder)):
            makedirs(self.file_folder, exist_ok=True)

    def get_report(self, year, month, market=MarketType.LISTED_STOCK):
        for_pd_csv = None
        tw_year = DateTool.to_tw_year(year)
        report_file_name = join(self.file_folder, f'monthly_revenue_{year}_{month}.html')

        if exists(report_file_name):
            for_pd_csv = report_file_name
        else:
            resp = requests.post(
                url='https://mops.twse.com.tw/server-java/FileDownLoad',
                data={
                    'step': '9',
                    'functionName': 'show_file2',
                    'filePath': self.FILE_PATH_MAPPING[market],
                    'fileName': f't21sc03_{tw_year}_{month}.csv'
                }
            )

            resp.encoding = 'utf-8'
            if resp.text[:2] == '﻿出':
                for_pd_csv = io.StringIO(resp.content.decode('utf-8'))
                with open(report_file_name, 'w') as f:
                    f.write(resp.text)
            else:
                return None

        time.sleep(random.randint(self.delay_initial, self.delay_max))
        return MonthlyRevenueReport(
            year=year,
            month=month,
            report_df=pd.read_csv(for_pd_csv),
            market=market
        )

    def get_last_month_report(self, market=MarketType.LISTED_STOCK):
        if self.today.month == 1:
            year, mon = (self.today.year - 1, 12)
        else:
            year, mon = (self.today.year, self.today.month - 1)

        return self.get_report(year, mon, market)


if __name__ == "__main__":
    mr_agent = MonthlyRevenueAgent()
    y2022_m12_mr = mr_agent.get_last_month_report()
    print(y2022_m12_mr.get_industry_mapping("食品工業"))
    # print(y2022_m12_mr.head(1)['公司代號'])
    # print(y2022_m12_mr.loc[y2022_m12_mr['公司代號'] == 1101])
