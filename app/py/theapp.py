
import os.path
import webapp2
import jinja2
from google.appengine.api import users

import blbr


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '..', 'template')))


class TemplatePage(webapp2.RequestHandler):

    login_required = True
    
    def make_context(self):
        return {}
    
    def get(self):
        requiring = self.login_required and blbr.require_login(redirect=self.url) or None
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

class TestPage(TemplatePage):
    url = '/test'
    login_required = False
    template_name = 'test.html'


page_classes = [IndexPage, DashboardPage, TestPage,
                blbr.UserController]

# Don't change the name |app|. It is given in the 'app.cfg' file.
app = blbr.to_application(page_classes)
