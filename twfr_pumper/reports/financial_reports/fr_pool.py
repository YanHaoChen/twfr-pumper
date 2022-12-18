from twfr_pumper.reports.financial_reports.financial_report_agent import FinancialReportAgent


class FRPool(object):
    def __init__(self):
        self.__agents = []
        self.reports = {}

    def add_agent(self, agent: FinancialReportAgent):
        self.__agents.append(agent)

    def add_range_reports(self, stock_id: str, report_type: str, start_y: int, start_s: int, end_y: int, end_s: int):
        start_y_s = start_y * 10 + start_s
        end_y_s = end_y * 10 + end_s
        while start_y_s <= end_y_s:
            self.add_agent(FinancialReportAgent(stock_id, start_y, start_s, report_type))
            start_s += 1
            if start_s == 5:
                start_s = 1
                start_y += 1

            start_y_s = start_y * 10 + start_s

    def organize_reports(self):
        for agent in self.__agents:
            year_season = agent.year * 10 + agent.season
            self.reports.setdefault(agent.company_id, {})
            self.reports[agent.company_id].setdefault(year_season, {'B': None, 'CI': None})
            self.reports[agent.company_id][year_season]['B'] = agent.balance_sheet.dict_format
            self.reports[agent.company_id][year_season]['CI'] = agent.comprehensive_income_sheet.dict_format

        self.__cal_roa_and_roe()
        return self.reports

    def __cal_roa_and_roe(self):
        for code, reports in self.reports.items():
            for y_and_s, report in reports.items():
                if y_and_s % 10 == 4:  # season 4
                    ex_y_and_s = y_and_s - 1
                    if ex_y_and_s not in reports.keys():
                        continue
                    ex_report = reports[ex_y_and_s]
                    ex_net_income = ex_report['CI']['8200']['value2']
                    s_net_income = report['CI']['8200']['value0'] - ex_net_income
                else:
                    s_net_income = report['CI']['8200']['value0']

                s_total_asset = report['B']['1XXX']['value0']
                s_total_equity = report['B']['3XXX']['value0']
                roa = round(s_net_income / s_total_asset * 100, 2)
                roe = round(s_net_income / s_total_equity * 100, 2)
                report.update({'roa': roa, 'roe': roe})


if __name__ == '__main__':

    pool = FRPool()
    pool.add_range_reports("2605", "C", 2020, 1, 2022, 3)
