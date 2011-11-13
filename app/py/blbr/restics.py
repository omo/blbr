
import webapp2
import json
import datetime
import re
import types

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
        return db.Model.put(self)

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


class ModelSerializer(object):
    to_map = {
        users.User: user_to_serializable,
        datetime.datetime: datetime_to_serializable,
        db.Key: key_to_serializable,
    }

    def __init__(self):
        self._property_name_cache = {}
        
    def _is_listable_property(self, property):
        # Don't list internal properties like db._ReverseReferenceProperty
        return isinstance(property, db.Property) and property.__class__.__name__[0] != '_'

    def _populate_property_names(self, list, cls):
        names = [k for k,v in cls.__dict__.items() if self._is_listable_property(v)]
        return list + names + reduce(self._populate_property_names, cls.__bases__, [])

    def property_names_for_class(self, cls):
        found = self._property_name_cache.get(cls)
        if found:
            return found
        names = self._populate_property_names([], cls)
        names.sort()
        self._property_name_cache[cls] = names
        return names

    def property_names_for(self, value):
        return self.property_names_for_class(value.__class__)

    def _serialize_property(self, property):
        # XXX: covnersion should be opt-in.
        to = self.to_map.get(property.__class__)
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
        
    def _build_serializable(self, value, dict):
        names = self.property_names_for(value)
        for name in names:
            dict[name] = self._serialize_property(getattr(value, name))
        return dict
    
    def to_serializable(self, obj):
        if isinstance(obj, types.ListType):
            return { "list": [self.to_serializable(i) for i in obj] }
        return self._build_serializable(obj, {"id": str(obj.key()) })


class Repo(object):
    @property
    def account(self):
        return users.get_current_user()

    @property
    def positional_count(self):
        return self.url_pattern.count("(")
    
    def has_full_positional(self, positionals):
        return len([p for p in positionals if p]) == self.positional_count


class Controller(webapp2.RequestHandler):

    @property
    def repo(self):
        if not hasattr(self, '_repo'):
            self._repo = self.repo_class()
        return self._repo

    @property
    def ser(self):
        if not hasattr(self, '_ser'):
            self._ser = ModelSerializer()
        return self._ser
        
    @wsgis.login_required
    def get(self, *args):
        found = self.repo.get(args)
        if None == found:
            self.response.status = 404
            return
        self.response.headers['Content-Type'] = 'text/json'
        json.dump(self.ser.to_serializable(found), self.response.out)

    @wsgis.login_required
    def put(self, *args):
        j = json.loads(self.request.body)
        created = self.repo.put(args, j)
        if not created:
            self.response.status = 400
            return
        self.response.headers['Content-Type'] = 'text/json'
        json.dump(self.ser.to_serializable(created), self.response.out)
        
    @classmethod
    def subclass_for(cls, a_repo_class):
        class ResticController(cls):
            url = a_repo_class.url_pattern
            repo_class = a_repo_class
        return ResticController
