
import os.path
import webapp2
import jinja2
from google.appengine.api import users

import blbr


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.join(os.path.dirname(__file__), '..', 'template')))


class TemplatePage(webapp2.RequestHandler):

    LOGIN_REQUIRED = True
    
    def make_context(self):
        return {}
    
    def get(self):
        user = users.get_current_user()
        if not user and self.LOGIN_REQUIRED:
            #raise Exception("Hello")
            self.response = webapp2.redirect(users.create_login_url(self.URL))
            return self.response

        template = jinja_environment.get_template(self.TEMPLATE_NAME)
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(template.render(self.make_context()))


class IndexPage(TemplatePage):
    URL = "/"
    TEMPLATE_NAME = 'index.html'
    LOGIN_REQUIRED = False
    
    def make_context(self):
        return {'login_url':  users.create_login_url(DashboardPage.URL)}


class DashboardPage(TemplatePage):
    URL = '/dashboard'
    TEMPLATE_NAME = 'dashboard.html'


page_classes = [IndexPage, DashboardPage]

# The name |app| is given at 'app.cfg' file.
app = webapp2.WSGIApplication([(p.URL, p) for p in page_classes])
