
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

    def find_by_keylike(self, keylike):
        if (keylike == "me"):
            return self.me
        try:
            found = User.get(db.Key(keylike))
            if not found or found.account != self.account:
                return None
            return found
        except db.BadKeyError:
            return None
        
    @property
    def me(self):
        return User.ensure_by_account(self.account)
        
    def get(self, positionals):
        if not self.has_full_positional(positionals):
            # XXX: Should handle list
            return None
        keylike = positionals[-1]
        return self.find_by_keylike(keylike)


UserController = restics.Controller.subclass_for(UserRepo)
