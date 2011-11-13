
import webapp2
import json
import datetime
import re

from google.appengine.api import users
from google.appengine.ext import db

import blbr.wsgis as wsgis


class Model(db.Model):
    @classmethod
    def _before_put(cls, target):
        # XXX: exract as a hook.
        now = datetime.datetime.now()
        if not target.created_at:
            target.created_at = now
        target.updated_at = now
        
    def put(self):
        self._before_put(self)
        db.Model.put(self)

def key_to_serializable(key):
    return str(key)

def user_to_serializable(user):
    return {
        "nickname": user.nickname(),
        "email": user.email(),
        "user_id": user.user_id()
    }

def datetime_to_serializable(d):
    return d.isoformat()


class ModelSerizable(object):
    to_map = {
        users.User: user_to_serializable,
        datetime.datetime: datetime_to_serializable,
        db.Key: key_to_serializable,
    }

    @staticmethod
    def _is_listable_property(property):
        # Don't list internal properties like db._ReverseReferenceProperty
        return isinstance(property, db.Property) and property.__class__.__name__[0] != '_'
    
    @staticmethod
    def _populate_property_names(list, cls):
        names = [k for k,v in cls.__dict__.items() if ModelSerizable._is_listable_property(v)]
        return list + names + reduce(ModelSerizable._populate_property_names, cls.__bases__, [])

    @classmethod
    def property_names(cls):
        if not hasattr(cls, '_propety_names'):
            cls._propety_names = ModelSerizable._populate_property_names([], cls)
            cls._propety_names.sort()
        return cls._propety_names

    @classmethod
    def _serialize_property(cls, property):
        # XXX: covnersion should be opt-in.
        to = ModelSerizable.to_map.get(property.__class__)
        if to:
            return to(property)
        # XXX: Sub-models should be security-aware.  For example, an
        # User properties should be only visible from its owner.
        # Returns key value for now.
        # Ideally we should access underlying db.Key object
        # directly without fetching the referencing object.
        if isinstance(property, db.Model):
            return str(property.key())
        return property
        
    @classmethod
    def _build_serializable(cls, value, dict):
        names = cls.property_names()
        for name in names:
            dict[name] = cls._serialize_property(getattr(value, name))
        return dict
    
    def to_serializable(self):
        #if isinstance(self, list):
        #    return { list: [i.to_serializable() for i in self] }
        return self._build_serializable(self, {"id": str(self.key()) })


class Repo(object):
    @property
    def account(self):
        return users.get_current_user()

    @property
    def positional_count(self):
        return self.url_pattern.count("(")
    
    def has_full_positional(self, params):
        return len(params) == self.positional_count


class Controller(webapp2.RequestHandler):
    @property
    def repo(self):
        if not hasattr(self, '_repo'):
            self._repo = self.repo_class()
        return self._repo

    @wsgis.login_required
    def get(self, *args):
        found = self.repo.get(args)
        if not found:
            self.response.status = 404
            return
        self.response.headers['Content-Type'] = 'text/json'
        json.dump(found.to_serializable(), self.response.out)
        return self.response

    @classmethod
    def subclass_for(cls, a_repo_class):
        class ResticController(cls):
            url = a_repo_class.url_pattern
            repo_class = a_repo_class
        return ResticController
