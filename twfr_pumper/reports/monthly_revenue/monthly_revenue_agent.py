import requests
import io
from os.path import exists, isdir, join
from os import makedirs

import pandas as pd

from twfr_pumper.toolbox.date_tool import DateTool


class MonthlyRevenueAgent(object):
    def __new__(cls, year, month, file_path="./tmp/monthly_revenue"):
        for_pd_csv = None
        tw_year = DateTool.to_tw_year(year)
        if not (exists(file_path) and isdir(file_path)):
            makedirs(file_path, exist_ok=True)

        report_file_name = join(file_path, f'monthly_revenue_{year}_{month}.html')

        if exists(report_file_name):
            for_pd_csv = report_file_name
        else:
            resp = requests.post(
                url='https://mops.twse.com.tw/server-java/FileDownLoad',
                data={
                    'step': '9',
                    'functionName': 'show_file2',
                    'filePath': '/t21/sii/',
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

        monthly_revenue_df = pd.read_csv(for_pd_csv)
        print(monthly_revenue_df['公司代號'])


if __name__ == "__main__":
    MonthlyRevenueAgent(2022, 11)