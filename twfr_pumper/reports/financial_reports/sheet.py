import abc
from functools import cached_property


class Sheet(abc.ABC):
    ID = "None"

    def __init__(self):
        self.magic_id = ""
        self.dollar_unit = 0
        self.sheet = None

    def set_dollar_unit(self, dollar_unit):
        self.dollar_unit = dollar_unit

    @property
    @abc.abstractmethod
    def magic_id(self):
        # for parse unit
        return NotImplementedError

    @cached_property
    def dict_format(self):
        result = {}
        row_codes = self.sheet.find_all('td', attrs={'style': 'text-align:center'})
        for row_code in row_codes:
            code = row_code.string.lstrip() if row_code.string else None
            if code and code != '-':
                siblings_tds = row_code.find_next_siblings('td')
                zh_td_span = siblings_tds[0].find('span', class_='zh')
                en_td_span = siblings_tds[0].find('span', class_='en')
                result[code] = {
                    'zh': zh_td_span.string.strip(),
                    'en': en_td_span.string.strip(),
                    'values': []
                }
                for idx, value_td in enumerate(siblings_tds[1:]):
                    value = value_td.find('ix:nonfraction').string.strip()
                    result[code]['values'].append(self.to_number(value))

        return result

    @staticmethod
    def to_number(value: str):
        number = value.replace(",", "")
        if '(' in number:
            return float(number[1:-1]) * -1.0
        else:
            return float(number)

    @staticmethod
    def sheet_str_to_number(result_dict: dict):
        for key, acc_number in result_dict.items():
            number = acc_number.replace(",", "")
            if '(' in number:
                result_dict[key] = float(number[1:-1]) * -1.0
            else:
                result_dict[key] = float(number)
