
import functools
import webapp2
import json
from google.appengine.ext import db
from google.appengine.api import users

def require_login(**options):
    if users.get_current_user():
        return None
    redirect = options.get('redirect')
    if redirect:
        return webapp2.redirect(users.create_login_url(redirect))
    resp = webapp2.Response()
    resp.status = '400 Bad Request'
    return resp
    
def login_required(func, **deco_kwargs):
    @functools.wraps(func)
    def decorated_view(*args, **kwargs):
        return require_login(**deco_kwargs) or func(*args, **kwargs)
    return decorated_view

def user_to_serializable(user):
    return {
        "nickname": user.nickname(),
        "email": user.email(),
        "user_id": user.user_id()
    }


class ModelSerizable(object):

    to_map = {
        users.User: user_to_serializable
    }
    
    @staticmethod
    def _build_property_name(list, base):
        if issubclass(base, ModelSerizable):
            list += base.list_property_names()
        return list

    @classmethod
    def list_property_names(cls):
        names  = [k for k,v in cls.__dict__.items() if isinstance(v, db.Property)]
        return reduce(cls._build_property_name, cls.__bases__, names)
    
    @classmethod
    def _build_serializable(cls, value, dict):
        names = cls.list_property_names()
        for name in names:
            value = getattr(value, name)
            to = ModelSerizable.to_map.get(value.__class__)
            dict[name] = to and to(value) or value
        return dict
    
    def to_serializable(self):
        return self._build_serializable(self, {"id": str(self.key()) })

        
class User(db.Model, ModelSerizable):
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


class UserMapper(object):
    def get_account(self):
        return users.get_current_user()
    
    def get(self, params):
        if (1 != len(params)):
            return users.create_login_url(self.url)
        
        account = self.get_account()
        key = params[0]
        if (key == "me"):
            return User.ensure_by_account(account)
        try:
            found = User.get(db.Key(key))
        except db.BadKeyError:
            return None
        if not found or found.account != account:
            return None
        return found

    
class UserController(webapp2.RequestHandler):
    url = '/r/([^/]+)'

    @property
    def mapper(self):
        if not hasattr(self, '_mapper'):
            self._mapper = UserMapper()
        return self._mapper

    @login_required
    def get(self, *args):
        found = self.mapper.get(args)
        if not found:
            self.response.status = 404
            return
        self.response.headers['Content-Type'] = 'text/json'
        json.dump(found.to_serializable(), self.response.out)
        return self.response


def to_application(handler_classes):
    return webapp2.WSGIApplication([(p.url, p) for p in handler_classes])
