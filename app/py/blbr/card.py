
from google.appengine.ext import db
from google.appengine.api import users

import blbr.restics as restics
import blbr.user

class Card(db.Model):
    # XXX: should be handled by the metaclass
    created_at = db.DateTimeProperty()
    updated_at = db.DateTimeProperty()

    owner = db.ReferenceProperty(required=True)
    face = db.TextProperty()
    back = db.TextProperty()

    @classmethod
    def find_by_owner(cls, owner):
        return cls.all().filter("owner = ", owner).fetch(100, 0)


class CardRepo(restics.Repo):
    url_pattern = '/r/([^/]+)/card(/([^/]+))?'

    def get(self, params):
        if len(params) < self.positional_count - 2:
            return None
        user_keylike = params[0]
        owner = blbr.user.UserRepo.find_by_keylike(user_keylike, self.account)
        if not owner:
            return None
        if not self.has_full_positional(params):
            return Card.find_by_owner(owner.key()) or []
        try:
            card_keylike = params[2]
            return Card.get(db.Key(card_keylike))
        except db.BadKeyError:
            return None


CardController = restics.Controller.subclass_for(CardRepo)
