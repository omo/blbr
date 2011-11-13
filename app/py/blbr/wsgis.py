
import functools
import webapp2

from google.appengine.api import users

def require_login(**kwargs):
    if users.get_current_user():
        return None
    redirect = kwargs.get('redirect')
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

def to_application(handler_classes):
    return webapp2.WSGIApplication([(p.url, p) for p in handler_classes])
