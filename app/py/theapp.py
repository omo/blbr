
import os.path
import webapp2
import jinja2
from google.appengine.api import users

import blbr
import blbr.wsgis


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '..', 'template')))


class TemplatePage(webapp2.RequestHandler):
    login_required = True
    
    def make_context(self):
        return {}

    def requiring(self):
        return self.login_required and blbr.wsgis.require_login(redirect=self.url) or None

    def get(self):
        requiring = self.requiring()
        if requiring:
            return requiring
        template = jinja_environment.get_template(self.template_name)
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(template.render(self.make_context()))
        return self.response


class IndexPage(TemplatePage):
    url = "/"
    template_name = 'index.html'
    login_required = False
    
    def make_context(self):
        return {'login_url':  users.create_login_url(DashboardPage.url)}


class DashboardPage(TemplatePage):
    url = '/dashboard'
    template_name = 'dashboard.html'

    def get(self):
        r = self.requiring()
        if r:
            return r
        me = blbr.User.ensure_by_account(users.get_current_user())
        blbr.Card.welcome(me)
        return TemplatePage.get(self)
        

class TestPage(TemplatePage):
    url = '/test'
    login_required = False
    template_name = 'test.html'


page_classes = [
    IndexPage,
    DashboardPage,
    TestPage,
    blbr.CardController, blbr.CardCollectionController,
    blbr.LevelController,
    blbr.UserController,
]

# Don't change the name |app|. It is given in the 'app.cfg' file.
app = blbr.wsgis.to_application(page_classes)
