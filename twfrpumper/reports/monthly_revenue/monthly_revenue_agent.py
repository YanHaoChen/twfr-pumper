import requests
import io
from os.path import exists, isdir, join
from os import makedirs
from datetime import date
from enum import Enum
from typing import Union

import pandas as pd

from twfrpumper.toolbox.date_tool import DateTool


class MarketType(Enum):
    LISTED_STOCK = 0
    OTC_MARKET = 1


class MonthlyRevenueReport(object):
    def __init__(self, year, month, report_df, market: MarketType):
        self.year = year
        self.month = month
        self.report_df = report_df
        self.market = market

    def get_industry_list(self):
        return self.report_df['產業別'].unique().tolist()

    def get_company_name_list(self):
        return self.report_df['公司名稱'].unique().tolist()

    def get_company_list_by_industry(self, industry: str):
        return self.report_df.loc[self.report_df['產業別'] == industry][['公司代號', '公司名稱']].values

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


class MonthlyRevenueAgent(object):
    FILE_PATH_MAPPING = {
        MarketType.LISTED_STOCK: '/t21/sii/',
        MarketType.OTC_MARKET: '/t21/otc/'
    }

    def __init__(self, file_folder="./tmp/monthly_revenue"):
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
