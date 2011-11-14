# -*- coding: utf-8 -*-
import logging
import copy

from google.appengine.ext import db
from google.appengine.api import users

import blbr.restics as restics
import blbr.user

WELCOME_CARDS = [
    { u"face": u"Welcome!", u"back": u"ようこそ!" },
    { u"face": u"The [bracket] is waiting for you.", u"back": u"[カッコ]があなたを待っています." },
]
            
class Card(restics.Model):
    # XXX: should be handled by the metaclass
    created_at = db.DateTimeProperty()
    updated_at = db.DateTimeProperty()

    owner = db.ReferenceProperty(required=True)
    face = db.TextProperty(required=True)
    back = db.TextProperty()

    def owned_by(self, mayowner):
        return self.owner.account == mayowner.account

    @classmethod
    def find_by_owner(cls, owner):
        return cls.all().filter("owner = ", owner).fetch(100, 0)

    @classmethod
    def welcome(cls, owner):
        founds = cls.find_by_owner(owner)
        if founds:
            return
        for c in WELCOME_CARDS:
            fresh = copy.copy(c)
            fresh["owner"] = owner
            Card(**fresh).put()
            

class CardRepo(restics.Repo):
    item_url_pattern = '/r/<user_id>/card/<card_id>'
    item_namespace = 'r/me/card'
    collection_url_pattern = '/r/<user_id>/card'
    collection_namespace = 'r/me/cards'
    
    def __init__(self):
        restics.Repo.__init__(self)
        self.parent = blbr.user.UserRepo()

    def delete_by_keylike(self, keylike):
        deleting = Card.get(db.Key(keylike))
        if (not deleting) or (not deleting.owned_by(self.parent.me)):
            return False
        deleting.delete()
        return True
    
    def update_by_bag(self, keylike, bag):
        updating = Card.get(db.Key(keylike))
        if (not updating) or (not updating.owned_by(self.parent.me)):
            return None
        if bag.get('face'):
            updating.face = bag.get('face')
        if bag.get('back'):
            updating.back = bag.get('back')
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

    def get(self, params):
        owner = self.parent.get(params)
        if not owner:
            logging.info(self.__class__.__name__, ".get: Missing owner")
            return None
        if not params.get('card_id'):
            logging.info(self.__class__.__name__, ".get: Missing card_id")
            return None
        try:
            return Card.get(db.Key(params['card_id']))
        except db.BadKeyError as e:
            logging.info(self.__class__.__name__, ".get: BadKeyError:", e)
            return None

    def list(self, params):
        owner = self.parent.get(params)
        if not owner:
            logging.info(self.__class__.__name__, ".get: Missing owner")
            return None
        return restics.CollectionEnvelope(
            self.collection_namespace,
            Card.find_by_owner(owner.key()) or [])


    def post(self, params, bag):
        owner = self.parent.get(params)
        if not owner:
            return None
        if params.get('card_id'):
            logging.info(self.__class__.__name__, ".post: Received redundnant ID for POST")
            return None
        try:
            return self.create_by_bag(owner, bag)
        except db.BadValueError as e:
            logging.info(self.__class__.__name__, ".post: BadValueError:", e)
            return None

    def put(self, params, bag):
        owner = self.parent.get(params)
        if not owner:
            logging.info(self.__class__.__name__, ".put: No owner")            
            return None
        if not params.get('card_id'):
            logging.info(self.__class__.__name__, ".put: Missing ID for PUT")
            return None
        try:
            return self.update_by_bag(params['card_id'], bag)
        except db.BadValueError as e:
            logging.info(self.__class__.__name__, ".put: BadValueError:", e)
            return None

    def delete(self, params):
        owner = self.parent.get(params)
        if not owner:
            return False
        if not params.get('card_id'):
            logging.info(self.__class__.__name__, ".delete: Missing ID for DELETE")
            return False
        try:
            return self.delete_by_keylike(params['card_id'])
        except db.BadValueError as e:
            logging.info(self.__class__.__name__, ".delete: BadValueError", e)
            return False


CardController = restics.item_controller_for(CardRepo)
CardCollectionController = restics.collection_controller_for(CardRepo)
