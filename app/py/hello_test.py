
import unittest
import os
import json
import webapp2

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import testbed

import blbr


def round_serialization(obj):
    return json.loads(json.dumps(obj))

class WSGITestHelper(object):

    def __init__(self, application):
        self.application = application

    def get(self, url):
        req = webapp2.Request.blank(url)
        return req.get_response(self.application)

class TestBedHelper(object):
    def __init__(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_user_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()        
        self.user_email = "alice@example.com"
        os.environ['USER_EMAIL'] = self.user_email

    def disable_current_user(self):
        if os.environ.get('USER_EMAIL'):
            del os.environ['USER_EMAIL']
        
    def deactivate(self):
        self.disable_current_user()
        self.testbed.deactivate()


class SerializableTest(unittest.TestCase):
    def setUp(self):
        self.helper = TestBedHelper()
        
    def tearDown(self):
        self.helper.deactivate()

    def test_hello(self):
        email = "bob@example.com"
        new_user = blbr.User(account=users.User(email))
        new_user.put()
        existing_user = blbr.User.find_by_account(new_user.account)
        rounded = round_serialization(existing_user.to_serializable())
        self.assertIsNotNone(rounded['id'])
        self.assertEquals(rounded['account']['email'], email)


class UserTest(unittest.TestCase, TestBedHelper):
    def setUp(self):
        self.helper = TestBedHelper()
        self.web = WSGITestHelper(blbr.to_application([blbr.UserController]))
        self.bob_email = "bob@example.com"

    def tearDown(self):
        self.helper.deactivate()

    def test_list_property_names(self):
        names = blbr.User.list_property_names()
        self.assertEquals(names, ['account'])

    def create_bob_user(self):
        account = users.User(self.bob_email)
        creating = blbr.User(account=account)
        creating.put()
        return creating

    def test_find_by_account(self):
        new_user = self.create_bob_user()
        existing_user = blbr.User.find_by_account(new_user.account)
        self.assertEquals(existing_user.account, new_user.account)

    def test_ensure(self):
        u = blbr.User.ensure_by_account(users.User("bob@example.com"))
        self.assertIsNotNone(u)
        self.assertTrue(u.is_saved())

    def test_web_get_me(self):
        res = self.web.get('/r/me')
        self.assertRegexpMatches(res.status, '200')
        self.assertEquals(self.helper.user_email, json.loads(res.body)["account"]["email"])

    def test_web_get_me(self):
        alice = blbr.User.ensure_by_account(users.get_current_user())
        res = self.web.get('/r/%s' % str(alice.key()))
        self.assertRegexpMatches(res.status, '200')
        self.assertEquals(self.helper.user_email, json.loads(res.body)["account"]["email"])

    def test_web_get_non_owner(self):
        bob = self.create_bob_user()
        res = self.web.get('/r/%s' % str(bob.key()))
        self.assertRegexpMatches(res.status, '404')

    def test_web_get_notfound(self):
        bob = self.create_bob_user()
        res = self.web.get('/r/nonexistent')
        self.assertRegexpMatches(res.status, '404')

    def test_web_unauth(self):
        self.helper.disable_current_user()
        res = self.web.get('/r/me')
        self.assertRegexpMatches(res.status, '400')

