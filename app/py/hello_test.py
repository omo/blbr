
import unittest

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import testbed

import blbr

class HelloTest(unittest.TestCase):

    def test_hello(self):
        pass


class UserTest(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_user_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()        

    def tearDown(self):
        self.testbed.deactivate()
        
    def test_hello(self):
        account = users.User("alice@example.com")
        new_user = blbr.User(account=account)
        new_user.put()

        existing_user = blbr.User.find_by_account(account)
        self.assertEquals(existing_user.account, new_user.account)
        
    def test_ensure(self):
        account = users.User("alice@example.com")
        u = blbr.User.ensure_by_account(account)
        self.assertIsNotNone(u)
