
import logging
from google.appengine.ext import db
from google.appengine.api import users

import blbr.restics as restics
import blbr.user

class Card(restics.Model):
    # XXX: should be handled by the metaclass
    created_at = db.DateTimeProperty()
    updated_at = db.DateTimeProperty()

    owner = db.ReferenceProperty(required=True)
    face = db.TextProperty(required=True)
    back = db.TextProperty()

    @classmethod
    def find_by_owner(cls, owner):
        return cls.all().filter("owner = ", owner).fetch(100, 0)


class CardRepo(restics.Repo):
    url_pattern = '/r/([^/]+)/card(/([^/]+))?'

    def __init__(self):
        restics.Repo.__init__(self)
        self.parent = blbr.user.UserRepo()

    def update_by_bag(self, keylike, bag):
        updating = Card.get(db.Key(keylike))
        if not updating:
            return None
        if bag.get('face'):
            updating.face = bag.get('face')
        if bag.get('back'):
            updating.face = bag.get('back')
        updating.put()
        return updating

    def create_by_bag(self, owner, bag):
        creating = Card(**{
            "owner": owner.key(),
            "face": bag.get("face"),
            "back": bag.get("back"),
        })
        creating.put()
        return creating
        
    def get(self, positionals):
        if len(positionals) < self.positional_count - 2:
            return None
        owner_keylike = positionals[0]
        owner = self.parent.find_by_keylike(owner_keylike)
        if not owner:
            return None
        if not self.has_full_positional(positionals):
            # No ID is given, so we return collecoooootion.
            return Card.find_by_owner(owner.key()) or []
        try:
            card_keylike = positionals[2]
            return Card.get(db.Key(card_keylike))
        except db.BadKeyError as e:
            logging.info("CardRepo.get: BadKeyError %s" % e)
            return None

    def put(self, positionals, bag):
        user_keylike = positionals[0]
        owner = self.parent.find_by_keylike(user_keylike)
        if not owner:
            return None
        try:
            if self.has_full_positional(positionals):
                return self.update_by_bag(positionals[-1], bag)
            return self.create_by_bag(owner, bag)
        except db.BadValueError as e:
            logging.info("CardRepo.put: BadValueError %s", e)
            return None


CardController = restics.Controller.subclass_for(CardRepo)
