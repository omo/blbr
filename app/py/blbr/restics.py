
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


class Repo(object):
    @property
    def account(self):
        return users.get_current_user()

    @property
    def positional_count(self):
        return self.url_pattern.count("(")
    
    def has_full_positional(self, positionals):
        return len([p for p in positionals if p]) == self.positional_count


class CollectionEnvelope(object):
    def __init__(self, namespace, list):
        self.namespace = namespace
        self.list = list


def _key_to_bag(key):
    return str(key)

def _user_to_bag(user):
    return {
        "nickname": user.nickname(),
        "email": user.email(),
        "user_id": user.user_id()
    }

def _datetime_to_bag(d):
    return d.isoformat()


class ModelSerializer(object):
    to_map = {
        users.User: _user_to_bag,
        datetime.datetime: _datetime_to_bag,
        db.Key: _key_to_bag,
    }

    def __init__(self):
        self._property_name_cache = {}
        
    def _is_listable_property(self, property):
        # Don't list internal properties like db._ReverseReferenceProperty
        return isinstance(property, db.Property) and property.__class__.__name__[0] != '_'

    def _populate_property_names(self, list, cls):
        names = [k for k,v in cls.__dict__.items() if self._is_listable_property(v)]
        if hasattr(cls, 'excluding_properties'):
            for e in cls.excluding_properties:
                names.remove(e)
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
        
    def _build_model_bag(self, value, dict):
        names = self.property_names_for(value)
        for name in names:
            dict[name] = self._serialize_property(getattr(value, name))
        return dict

    def _build_collection_bag(self, env):
        return {
            env.namespace: [ self.to_bag(i) for i in env.list ]
        }

    def to_bag(self, obj):
        if isinstance(obj, CollectionEnvelope):
            return self._build_collection_bag(obj)
        if isinstance(obj, db.Model):
            return self._build_model_bag(obj, {"id": str(obj.key()) })
        if hasattr(obj, 'to_bag'):
            return obj.to_bag()
        raise Exception("Couldn't convert to a bag")
        


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

    def _get_or_list(self, method, args, kwargs):
        found = method(kwargs)
        if None == found:
            self.response.status = 404
            return
        self.response.headers['Content-Type'] = 'text/json'
        json.dump(self.ser.to_bag(found), self.response.out)

    def _post_or_put(self, method, args, kwargs):
        j = json.loads(self.request.body)
        created = method(kwargs, j[self.repo.item_namespace])
        if not created:
            self.response.status = 400
            return
        self.response.headers['Content-Type'] = 'text/json'
        json.dump(self.ser.to_bag(created), self.response.out)


class ItemController(Controller):
    @wsgis.login_required
    def delete(self, *args, **kwargs):
        if not self.repo.delete(kwargs):
            self.response.status = 400
            return
        self.response.status = 200

    @wsgis.login_required
    def put(self, *args, **kwargs):
        return self._post_or_put(self.repo.put, args, kwargs)

    @wsgis.login_required
    def get(self, *args, **kwargs):
        return self._get_or_list(self.repo.get, args, kwargs)
    

class CollectionController(Controller):
    @wsgis.login_required
    def post(self, *args, **kwargs):
        return self._post_or_put(self.repo.post, args, kwargs)

    @wsgis.login_required
    def get(self, *args, **kwargs):
        return self._get_or_list(self.repo.list, args, kwargs)


def controller_for(a_repo_class):
    class ResticItemController(ItemController):
        url = a_repo_class.url_pattern
        repo_class = a_repo_class
    return ResticItemController


def collection_controller_for(a_repo_class):
    class ResticCollectionController(CollectionController):
        url = a_repo_class.collection_url_pattern
        repo_class = a_repo_class
    return ResticCollectionController
