from dataclasses import dataclass, asdict
from os import makedirs, path
import logging

import pandas as pd
import plotly.express as px

from twfrpumper.reports.financial_reports.financial_report_agent import FinancialReportAgent
from twfrpumper.reports.financial_reports.financial_report_agent import FinancialReport


@dataclass
class DFRecord:
    code: str
    company_name: str
    y_and_s: str
    item: str
    zh: str
    en: str
    value: float = 0.0


class FRPool(object):
    def __init__(self):
        self.__agent = FinancialReportAgent()
        self.reports = set()
        self.organized_report = {}
        self.report_df = None
        self.name_mapping = {}

    def __cal_metrics_and_to_df(self):
        arr_for_df = []
        for code, reports in self.organized_report.items():
            for y_and_s, report in reports.items():
                self.__special_case_for_season_4(y_and_s, reports, report)
                self.__special_case_for_season_1_and_4(y_and_s, reports, report)
                self.__cal_dbr(report)
                self.__prepare_df_arr(code, y_and_s, reports, report, arr_for_df)

        if self.report_df:
            self.report_df = self.report_df.append(pd.DataFrame(arr_for_df), ignore_index=True)
            self.report_df = self.report_df.drop_duplicates()
        else:
            self.report_df = pd.DataFrame(arr_for_df)

    @staticmethod
    def __prepare_df_arr_for_common(code, company_name, y_and_s, item, object_, arr_for_df):
        str_y_and_s = str(y_and_s)
        zh = object_['zh']
        en = object_['en']
        record = DFRecord(
            code=code,
            company_name=company_name,
            y_and_s=str_y_and_s,
            item=item,
            zh=zh,
            en=en,
            value=object_['values'][0]
        )
        arr_for_df.append(asdict(record))

    @staticmethod
    def __prepare_df_arr_for_ci_sheet(code, company_name, y_and_s, reports, report, item, object_, arr_for_df):
        zh = object_['zh']
        en = object_['en']
        str_y_and_s = str(y_and_s)
        record = DFRecord(
            code=code,
            company_name=company_name,
            y_and_s=str_y_and_s,
            item=item,
            zh=zh,
            en=en,
            value=object_['values'][0]
        )
        if y_and_s % 10 == 4:
            ex_report = reports.get(y_and_s - 1, None)
            if ex_report and item in ex_report:
                # For EPS
                if item == '9750':
                    val_3100 = report['3100']['values'][0]
                    val_8200 = report['8200']['values'][0] - ex_report['8200']['values'][2]
                    value = val_8200 / (val_3100 / 10)
                elif item == '9850':
                    val_3110 = report['3110']['values'][0]
                    val_8200 = report['8200']['values'][0] - ex_report['8200']['values'][2]
                    value = val_8200 / (val_3110 / 10)
                else:
                    value = object_['values'][0] - ex_report[item]['values'][2]
                record.value = value
                arr_for_df.append(asdict(record))
            else:
                record.item = f'y_{item}'
                arr_for_df.append(asdict(record))
        else:
            arr_for_df.append(asdict(record))

    @staticmethod
    def __prepare_df_arr_for_cash_flows(code, company_name, y_and_s, reports, item, object_, arr_for_df):
        zh = object_['zh']
        en = object_['en']
        str_y_and_s = str(y_and_s)
        record = DFRecord(
            code=code,
            company_name=company_name,
            y_and_s=str_y_and_s,
            item=item,
            zh=zh,
            en=en,
            value=object_['values'][0]
        )
        if y_and_s % 10 == 1:
            arr_for_df.append(asdict(record))
        else:
            ex_report = reports.get(y_and_s - 1, None)
            if ex_report and item in ex_report:
                value = object_['values'][0] - ex_report[item]['values'][0]
                record.value = value
                arr_for_df.append(asdict(record))
            else:
                record.item = f'acc_{item}'
                arr_for_df.append(asdict(record))

    def __prepare_df_arr(self, code, y_and_s, reports, report, arr_for_df):
        company_name = f'{code}-{self.name_mapping[code]}'
        for item, object_ in report.items():
            if '4000' <= item <= '9850':
                self.__prepare_df_arr_for_ci_sheet(code, company_name, y_and_s, reports, report, item, object_, arr_for_df)
            elif 'A00010' <= item <= 'E00210':
                self.__prepare_df_arr_for_cash_flows(code, company_name, y_and_s, reports, item, object_, arr_for_df)
            else:
                self.__prepare_df_arr_for_common(code, company_name, y_and_s, item, object_, arr_for_df)

    def add_report(self, report: FinancialReport):
        if report:
            self.reports.add(report)
            if report.stock_id not in self.name_mapping:
                self.name_mapping.update({report.stock_id: report.company_name})

    def add_range_reports(self, stock_id: str, report_type: str, start_y: int, start_s: int, end_y: int, end_s: int):
        start_y_s = start_y * 10 + start_s
        end_y_s = end_y * 10 + end_s
        while start_y_s <= end_y_s:
            self.add_report(self.__agent.get_report(stock_id, start_y, start_s, report_type))
            start_s += 1
            if start_s == 5:
                start_s = 1
                start_y += 1

            start_y_s = start_y * 10 + start_s

    def organize_reports(self) -> None:
        for report in self.reports:
            year_season = report.year * 10 + report.season
            self.organized_report.setdefault(report.stock_id, {})
            self.organized_report[report.stock_id].update({year_season: report.balance_sheet.dict_format})
            self.organized_report[report.stock_id][year_season].update(report.ci_sheet.dict_format)
            self.organized_report[report.stock_id][year_season].update(report.cash_flows.dict_format)

        self.__cal_metrics_and_to_df()

    def list_items(self):
        return self.report_df[['item', 'zh', 'en']].drop_duplicates().values.tolist()

    def save_as_csv(self, file_path):
        folders = path.dirname(file_path)
        makedirs(folders, exist_ok=True)
        self.report_df.to_csv(file_path, index=False)

    def load_csv(self, file_path: str):
        if path.exists(file_path) and file_path.endswith('.csv'):
            loaded_df = pd.read_csv(file_path)
            loaded_df['y_and_s'] = loaded_df['y_and_s'].astype(str)
            if self.report_df:
                self.report_df = self.report_df.append(pd.DataFrame(loaded_df), ignore_index=True)
                self.report_df = self.report_df.drop_duplicates()
            else:
                self.report_df = pd.DataFrame(loaded_df)
        else:
            logging.error(f'{file_path} is not exist or not a csv.')

    def draw(self, item, title_lang='zh', multiple=1, adjust=1):

        item_df = self.report_df[(self.report_df.item == item)].sort_values(by=['y_and_s'])
        item_df['value'] *= multiple
        item_df['value'] += adjust
        fig = px.line(item_df,
                      x='y_and_s',
                      y='value',
                      color='company_name',
                      title=f'{item_df.iloc[0][title_lang]}, Adjust: {adjust}, Multiple: {multiple}')
        fig.show()

    def extend_item(self, *items, func, item_name, zh, en):
        items_df = []
        first_item_df = self.report_df[(self.report_df.item == items[0])]
        for item in items:
            items_df.append(self.report_df[(self.report_df.item == item)].sort_values(by=['y_and_s'])['value'].values)

        result_values = func(*items_df)
        new_item = first_item_df.copy()
        new_item['item'] = [item_name] * result_values.size
        new_item['zh'] = [zh] * result_values.size
        new_item['en'] = [en] * result_values.size
        new_item['value'] = result_values
        if self.report_df[(self.report_df.item == item_name)].size:
            self.report_df = self.report_df.drop(self.report_df[self.report_df.item == item_name].index)

        self.report_df = pd.concat([self.report_df, new_item], ignore_index=True)

    @staticmethod
    def __special_case_for_season_4(y_and_s, reports, report):
        if y_and_s % 10 == 4:  # season 4
            ex_y_and_s = y_and_s - 1
            if ex_y_and_s not in reports:
                return
            ex_report = reports[ex_y_and_s]

            ex_gross_profit = ex_report['5900']['values'][2]
            s_gross_profit = report['5900']['values'][0] - ex_gross_profit

            ex_total_operating_revenue = ex_report['4000']['values'][2]
            s_total_operating_revenue = report['4000']['values'][0] - ex_total_operating_revenue

            ex_net_operating_income = ex_report['6900']['values'][2]
            s_net_operating_income = report['6900']['values'][0] - ex_net_operating_income

            ex_profit = ex_report['8200']['values'][2]
            s_profit = report['8200']['values'][0] - ex_profit
        else:
            s_total_operating_revenue = report['4000']['values'][0]
            s_gross_profit = report['5900']['values'][0]
            s_net_operating_income = report['6900']['values'][0]
            s_profit = report['8200']['values'][0]

        s_total_asset = report['1XXX']['values'][0]
        s_total_equity = report['3XXX']['values'][0]
        s_roa = round((s_profit / s_total_asset) * 100, 2)
        s_roe = round((s_profit / s_total_equity) * 100, 2)
        s_gross_margin = round((s_gross_profit / s_total_operating_revenue) * 100, 2)
        s_operating_margin = round((s_net_operating_income / s_total_operating_revenue) * 100, 2)
        s_net_profit_margin = round((s_profit / s_total_operating_revenue) * 100, 2)

        report.update({
            's_roa': {
                'zh': 'ROA(季)',
                'en': 'ROA(Season)',
                'values': [s_roa]
            },
            's_roe': {
                'zh': 'ROE(季)',
                'en': 'ROE(Season)',
                'values': [s_roe]
            },
            's_gross_margin': {
                'zh': '毛利率(季)',
                'en': 'Gross Margin(Season)',
                'values': [s_gross_margin]
            },
            's_operating_margin': {
                'zh': '營業利益率(季)',
                'en': 'Operating Margin(Season)',
                'values': [s_operating_margin]
            },
            's_net_profit_margin': {
                'zh': '淨利率(季)',
                'en': 'Net Profit Margin(Season)',
                'values': [s_net_profit_margin]
            },
        })

    @staticmethod
    def __cal_dbr(report):
        report.update({
            'dbr': {
                'zh': '負債比率',
                'en': 'Debt Burden Ratio',
                'values': [round((report['2XXX']['values'][0] / report['1XXX']['values'][0]) * 100, 2)]
            }
        })

    @staticmethod
    def __special_case_for_season_1_and_4(y_and_s, reports, report):
        ex_y_and_s = y_and_s - 1 if y_and_s % 10 != 1 else y_and_s - 7
        if ex_y_and_s not in reports.keys():
            return

        ex_s_report = reports[ex_y_and_s]
        curr_inventories = report['130X']['values'][0]
        ex_s_curr_inv = ex_s_report['130X']['values'][0] if '130X' in ex_s_report else 0
        avg_inv = (curr_inventories + ex_s_curr_inv) / 2

        if y_and_s % 10 == 4:
            curr_toc = report['5000']['values'][0]
            ex_s_acc_toc = ex_s_report['5000']['values'][2] if '5000' in ex_s_report else 0
            s_total_operating_costs = curr_toc - ex_s_acc_toc
        else:
            s_total_operating_costs = report['5000']['values'][0]

        s_it = round(s_total_operating_costs / avg_inv, 2) if avg_inv else 0
        s_it_days = round(90 / s_it, 2) if s_it else 0
        report.update({
            's_it': {
                'zh': 's_it',
                'en': 's_inventory_turnover',
                'values': [s_it]
            },
            's_it_days': {
                'zh': 's_it_days',
                'en': 's_inventory_turnover_days',
                'values': [s_it_days]
            }
        })


if __name__ == '__main__':
    pool = FRPool()
    pool.add_range_reports("2605", "C", 2020, 1, 2021, 4)
    pool.organize_reports()


