
import logging

from google.appengine.ext import db
from google.appengine.api import users

import blbr.restics as restics

class Level(object):
    placeholder_id = 'latest'
    
    def __init__(self, round):
        self.round = round

    def to_bag(self):
        return { 'round': self.round, 'id': self.id }

    @property
    def id(self):
        return self.placeholder_id
    
    def updated_by_bag(self, bag):
        return Level(bag.get('round') or self.round)


class User(restics.Model):
    # XXX: should be handled by the metaclass
    created_at = db.DateTimeProperty()
    updated_at = db.DateTimeProperty()
    
    account = db.UserProperty(required=True)
    level_round = db.IntegerProperty(default=1, required=True) # The default should be 0. This value is a workaround for batman.js.
    
    excluding_properties = ['level_round']
    
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

    @property
    def level(self):
        return Level(round=self.level_round)

    def put_level(self, level):
        self.level_round = level.round
        self.put()


class UserRepo(restics.Repo):
    item_url_pattern = '/r/<user_id>'

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
        
    def get(self, params):
        if not params.get('user_id'):
            logging.info(self.__class__.__name__, '.get: Missing user_id')
            return None
        return self.find_by_keylike(params['user_id'])
        

UserController = restics.item_controller_for(UserRepo)
