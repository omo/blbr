
from google.appengine.ext import db
from google.appengine.api import users

import blbr.restics as restics

class User(restics.Model):
    # XXX: should be handled by the metaclass
    created_at = db.DateTimeProperty()
    updated_at = db.DateTimeProperty()

    account = db.UserProperty(required=True)
   
    @classmethod
    def find_by_account(cls, account):
        return cls.all().filter("account =", account).get()

    @classmethod
    def ensure_by_account(cls, account):
        found = cls.find_by_account(account)
        if found:
            return found
        created = cls(account=account)
        created.put()
        return created

class UserRepo(restics.Repo):
    url_pattern = '/r(/([^/]+))?'

    @classmethod
    def find_by_keylike(cls, keylike, me):
        if (keylike == "me"):
            return User.ensure_by_account(me)
        try:
            found = User.get(db.Key(keylike))
        except db.BadKeyError:
            return None
        if not found or found.account != me:
            return None
        return found
        
    def get(self, params):
        if not self.has_full_positional(params):
            # XXX: Should handle list
            return None
        keylike = params[-1]
        return self.find_by_keylike(keylike, self.account)

UserController = restics.Controller.subclass_for(UserRepo)
