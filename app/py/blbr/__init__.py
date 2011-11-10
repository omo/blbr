
from google.appengine.ext import db


class User(db.Model):
    account = db.UserProperty(required=True)

    @classmethod
    def find_by_account(cls, account):
        return cls.all().filter("account =", account).get()

    @classmethod
    def ensure_by_account(cls, account):
        return cls.find_by_account(account) or cls(account=account)
