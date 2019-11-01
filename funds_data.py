class FundInfo():
    def __init__(self, name, percentage, value):
        self.name = name
        self.percentage = percentage
        self.value = value
    def __str__(self):
        return self.name + '; ' + str(self.percentage) + '; ' + str(self.value)

class Security():
    def __init__(self, isin, sec_type, name, currency, percentage):
        self.isin = isin
        self.sec_type = sec_type
        self.name = name
        self.currency = currency
        self.percentage = percentage
        self.funds = []
    def add_fund(self, fund_info):
        self.funds.append(fund_info)
    def __str__(self):
        ret_str = self.isin + ' - ' + self.sec_type + ' - ' + self.name + ' - ' + self.currency  + ' - ' + str(self.percentage)
        if (len(self.funds) > 0):
            ret_str += ' ### funds: '
            for fund_info in self.funds:
                ret_str += str(fund_info) + ' ## '
        return ret_str
