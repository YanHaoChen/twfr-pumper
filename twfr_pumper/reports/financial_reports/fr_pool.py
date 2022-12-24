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

        self.__cal_metrics()
        return self.reports

    def __cal_metrics(self):
        for code, reports in self.reports.items():
            for y_and_s, report in reports.items():
                self.__cal_roa_and_roe(y_and_s, reports, report)
                self.__cal_inventory_turnover(y_and_s, reports, report)

    @staticmethod
    def __cal_roa_and_roe(y_and_s, reports, report):
        if y_and_s % 10 == 4:  # season 4
            ex_y_and_s = y_and_s - 1
            if ex_y_and_s not in reports.keys():
                return
            ex_report = reports[ex_y_and_s]
            ex_profit = ex_report['CI']['8200']['values'][2]
            s_profit = report['CI']['8200']['values'][0] - ex_profit
        else:
            s_profit = report['CI']['8200']['values'][0]

        s_total_asset = report['B']['1XXX']['values'][0]
        s_total_equity = report['B']['3XXX']['values'][0]
        s_roa = round(s_profit / s_total_asset * 100, 2)
        s_roe = round(s_profit / s_total_equity * 100, 2)
        report.update({'s_roa': s_roa, 's_roe': s_roe})

    @staticmethod
    def __cal_inventory_turnover(y_and_s, reports, report):
        ex_y_and_s = y_and_s - 1 if y_and_s % 10 != 1 else y_and_s - 7
        if ex_y_and_s not in reports.keys():
            return

        ex_s_report = reports[ex_y_and_s]
        curr_inventories = report['B']['130X']['values'][0]
        ex_s_curr_inv = ex_s_report['B']['130X']['values'][0]
        avg_inv = (curr_inventories + ex_s_curr_inv) / 2

        if y_and_s % 10 == 4:
            curr_toc = report['CI']['5000']['values'][0]
            ex_s_acc_toc = ex_s_report['CI']['5000']['values'][2]
            s_total_operating_costs = curr_toc - ex_s_acc_toc
        else:
            s_total_operating_costs = report['CI']['5000']['values'][0]

        s_it = round(s_total_operating_costs / avg_inv, 2)
        s_it_day = round(90 / s_it, 2)
        report.update({'s_it': s_it, 's_it_days': s_it_day})


if __name__ == '__main__':
    pool = FRPool()
    pool.add_range_reports("2605", "C", 2020, 1, 2022, 3)
    pool.organize_reports()
    print(pool.reports['2605'][20223]['s_it_days'])
    print(pool.reports['2605'][20222]['s_it_days'])
    print(pool.reports['2605'][20221]['s_it_days'])
    print(pool.reports['2605'][20214]['s_it_days'])
    print(pool.reports['2605'][20213]['s_it_days'])
    print(pool.reports['2605'][20204]['s_it_days'])


