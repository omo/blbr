
import unittest
import os
import json
import webapp2

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import testbed

import blbr
import blbr.restics


def round_serialization(obj):
    return json.loads(json.dumps(obj))

class WSGITestHelper(object):
    def __init__(self, application):
        self.application = application

    def get(self, url):
        req = webapp2.Request.blank(url)
        return req.get_response(self.application)

    def put(self, url, body):
        return self._request_with_body(url, 'PUT', body)

    def post(self, url, body):
        return self._request_with_body(url, 'POST', body)

    def delete(self, url):
        req = webapp2.Request.blank(url)
        req.method = 'DELETE'
        return req.get_response(self.application)

    def _request_with_body(self, url, method, body):
        req = webapp2.Request.blank(url)
        req.body = body
        req.method = method
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

    def create_current_user_model(self):
        return blbr.User.ensure_by_account(users.get_current_user())


class SerializableTest(unittest.TestCase):
    def setUp(self):
        self.helper = TestBedHelper()
        self.ser = blbr.restics.ModelSerializer()

    def tearDown(self):
        self.helper.deactivate()

    def test_hello(self):
        email = "bob@example.com"
        new_user = blbr.User(account=users.User(email))
        self.assertEquals(new_user.level_round, 0)
        new_user.put()
        existing_user = blbr.User.find_by_account(new_user.account)
        rounded = round_serialization(self.ser.to_bag(existing_user))
        self.assertIsNotNone(rounded['id'])
        self.assertIsNone(rounded.get('level_round'))
        self.assertEquals(rounded['account']['email'], email)


class UserTest(unittest.TestCase):
    def setUp(self):
        self.helper = TestBedHelper()
        self.web = WSGITestHelper(blbr.wsgis.to_application([blbr.UserController]))
        self.bob_email = "bob@example.com"

    def tearDown(self):
        self.helper.deactivate()

    def test_property_names(self):
        ser = blbr.restics.ModelSerializer()
        names = ser.property_names_for_class(blbr.User)
        self.assertEquals(names, ['account', 'created_at', 'updated_at'])

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

    def test_web_list(self):
        res = self.web.get('/r')
        self.assertRegexpMatches(res.status, '404')

    def test_web_get_me(self):
        res = self.web.get('/r/me')
        self.assertRegexpMatches(res.status, '200')
        self.assertEquals(self.helper.user_email, json.loads(res.body)["account"]["email"])

    def test_web_get_me(self):
        alice = self.helper.create_current_user_model()
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


class LevelTest(unittest.TestCase):
    def setUp(self):
        self.helper = TestBedHelper()
        self.web = WSGITestHelper(blbr.wsgis.to_application([blbr.LevelController]))

    def tearDown(self):
        self.helper.deactivate()

    def test_get_hello(self):
        res = self.web.get('/r/me/level')
        self.assertRegexpMatches(res.status, '200')
        j = json.loads(res.body)
        self.assertEquals(j['round'], 0)

    def test_put_hello(self):
        res = self.web.put('/r/me/level', json.dumps({'r/me/level': { 'round': 5 }}))
        self.assertRegexpMatches(res.status, '200')
        self.assertEquals(json.loads(res.body)['round'], 5)
        self.assertEquals(json.loads(self.web.get('/r/me/level').body)['round'], 5)


class CardFixture(object):
    def __init__(self, owner):
        self.keys = []
        self.keys.append(blbr.Card(owner=owner.key(), face="Hello", back="Konnichiwa").put())
        self.keys.append(blbr.Card(owner=owner.key(), face="Good bye", back="Sayonara").put())        


class CardTest(unittest.TestCase):
    def setUp(self):
        self.helper = TestBedHelper()
        self.web = WSGITestHelper(blbr.wsgis.to_application([blbr.CardController,
                                                             blbr.CardCollectionController]))
        
        self.bob_email = "bob@example.com"
        self.alice = self.helper.create_current_user_model()
        self.alice_fixture = CardFixture(self.alice)
        self.bob = blbr.User.ensure_by_account(account=users.User(email=self.bob_email))
        self.bob_fixture = CardFixture(self.bob)
                                   
    def tearDown(self):
        self.helper.deactivate()

    def assert_looking_like_a_card(self, cardlike, face="Hello", back="Konnichiwa"):
        self.assertIsNotNone(cardlike["id"])
        self.assertEquals(cardlike["face"], face)
        self.assertEquals(cardlike["back"], back)

    def test_web_list(self):
        res = self.web.get('/r/%s/card' % str(self.alice.key()))
        self.assertRegexpMatches(res.status, '200')
        j = json.loads(res.body)
        self.assertEquals(len(j["r/me/cards"]), 2)
        self.assertEquals(j["r/me/cards"][0]["face"], 'Hello')

    def test_welcome(self):
        [c.delete() for c in blbr.Card.all().fetch(100, 0)]
        blbr.Card.welcome(self.alice)
        self.assertEquals(len(blbr.Card.find_by_owner(self.alice)), 2)
        
    def test_web_hello(self):
        res = self.web.get('/r/me/card/%s' % str(self.alice_fixture.keys[0]))
        self.assertRegexpMatches(res.status, '200')
        j = json.loads(res.body)
        self.assert_looking_like_a_card(j)
        

    fresh_card_literal = {"r/me/card": {'face': 'Hello'}}
    updating_card_literal = {"r/me/card": {'face': 'Hello Again', 'back': 'Konnichiwa Matane' }}
    
    def test_web_post_new(self):
        res = self.web.post('/r/me/card', json.dumps(self.fresh_card_literal))
        self.assertRegexpMatches(res.status, '200')
        j = json.loads(res.body)
        self.assert_looking_like_a_card(j, "Hello", None)

    def test_web_post_existing(self):
        existing_key = self.alice_fixture.keys[0]
        res = self.web.post('/r/me/card/%s' % str(self.alice_fixture.keys[0]), json.dumps(self.updating_card_literal))
        self.assertRegexpMatches(res.status, '405')

    def test_web_put_new(self):
        res = self.web.put('/r/me/card', json.dumps({"r/me/card": {'face': 'Hello'}}))
        self.assertRegexpMatches(res.status, '405')

    def test_web_put_new_for_someone(self):
        res = self.web.put('/r/%s/card' % str(self.bob.key()), json.dumps(self.fresh_card_literal))
        self.assertRegexpMatches(res.status, '405')

    def test_web_put_update(self):
        existing_key = self.alice_fixture.keys[0]
        res = self.web.put('/r/me/card/%s' % str(existing_key), json.dumps(self.updating_card_literal))
        self.assertRegexpMatches(res.status, '200')
        json.loads(res.body)
        updated = blbr.Card.get(existing_key)
        self.assertEquals(updated.key(), existing_key)
        self.assertEquals(updated.face, 'Hello Again')
        self.assertEquals(updated.back, 'Konnichiwa Matane')

    def test_web_put_for_bad_owner(self):
        bad_key = self.bob_fixture.keys[0]
        res = self.web.put('/r/me/card/%s' % str(bad_key), json.dumps(self.updating_card_literal))
        self.assertRegexpMatches(res.status, '400')

    def test_web_post_bad(self):
        res = self.web.post('/r/me/card', json.dumps({"r/me/card": {'foo': 'bar'}}))
        self.assertRegexpMatches(res.status, '400')
        
    def test_delete(self):
        existing_key = self.alice_fixture.keys[0]
        self.assertEquals(len(blbr.Card.find_by_owner(self.alice.key())), 2)
        res = self.web.delete('/r/me/card/%s' % str(existing_key))
        self.assertRegexpMatches(res.status, '200')
        self.assertEquals(len(blbr.Card.find_by_owner(self.alice.key())), 1)
