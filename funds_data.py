from mongoengine import EmbeddedDocument, EmbeddedDocumentField, Document, FloatField, IntField, ListField, StringField, connect

DATABASE_NAME = 'cnmv_funds'

class FundInfo(EmbeddedDocument):
    name = StringField(required=True)
    percentage = FloatField(required=True)
    value = IntField(required=True)
    def __str__(self):
        return self.name + '; ' + str(self.percentage) + '; ' + str(self.value)
    

class Security(Document):
    isin = StringField(max_length=12, required = True)
    sec_type = StringField(required = True)
    name = StringField(required = True)
    currency = StringField(max_length = 3, required = True)
    percentage = FloatField(required = True)
    funds = ListField(EmbeddedDocumentField(FundInfo))
    def add_fund(self, fund_info):
        self.funds.append(fund_info)
    def __str__(self):
        ret_str = self.isin + ' - ' + self.sec_type + ' - ' + self.name + ' - ' + self.currency  + ' - ' + str(self.percentage)
        if (len(self.funds) > 0):
            ret_str += ' ### funds: '
            for fund_info in self.funds:
                ret_str += str(fund_info) + ' ## '
        return ret_str

connect(DATABASE_NAME, host='localhost', port=27017)
