
class FakingAjaxSend
  constructor: ->
    @sent_reqs = []
    @original = Batman.Request::send
    self = this
    Batman.Request::send = (data) ->
      self.last_data = data
      self.sent_reqs.push(this)
      @fire 'loading'
  dispose: ->
    Batman.Request::send = @original
  respond: (status, resp) ->
    first = @sent_reqs.shift()
    first.set 'status', status
    first.set 'response', resp
    first.fire 'success', resp
    first.fire 'loaded'
  respond_a_one_item_collection: ->
    @respond(200, { "r/me/cards": ["id": "foo"] })

make_fixture_card = ->
  card = new Blbr.Card(next_round: 10, pass_count: 1, fail_count: 2, succession: 3)
  card.set('last_round', 20)
  card

asyncTest "Instantiate Card model", ->
  faking = new FakingAjaxSend()
  ret = Blbr.Card.get('all')
  setTimeout ->
    equal(1, faking.sent_reqs.length)
    faking.respond_a_one_item_collection()
    equal(ret.reduce().get("id"), "foo")
    start()

asyncTest "Card.round should request to the corresponding url", ->
  faking = new FakingAjaxSend()
  ret = Blbr.Card.get('round')
  setTimeout ->
    equal(1, faking.sent_reqs.length)
    equal(faking.sent_reqs[0].url, "/r/me/card")
    equal(faking.sent_reqs[0].data.sort, "round")
    faking.respond_a_one_item_collection()
    start()

test "Card.scoreAsPass", ->
  card = make_fixture_card()
  card.scoreAsPass()
  equal(card.get("next_round"), 24)
  equal(card.get("pass_count"),  2)
  equal(card.get("fail_count"),  2)
  equal(card.get("succession"),  4)

test "Card.scoreAsFail", ->
  card = make_fixture_card()
  card.scoreAsFail()
  equal(card.get("next_round"), 10)
  equal(card.get("pass_count"),  1)
  equal(card.get("fail_count"),  3)

test "Card doJudge", ->
  card = make_fixture_card()
  card.set("face", "foo [bar]")
  ok(!card.doJudge())
  card.face_fragments.toArray()[1].fill("baz")
  ok(!card.doJudge())
  card.face_fragments.toArray()[1].fill("bar")
  ok( card.doJudge())

test "CardFragment hello", ->
  f = Blbr.CardFragment.split("hello")
  equal(1, f.length)
  equal("hello", f[0].get('text'))
  ok(!f[0].get('blank'))

test "CardFragment middle hole", ->
  f = Blbr.CardFragment.split("foo [bar] baz")
  equal(3, f.length)
  equal("foo ", f[0].get('text'))
  equal("bar",  f[1].get('text'))
  equal(" baz", f[2].get('text'))

test "CardFragment side hole", ->
  f = Blbr.CardFragment.split("[foo] bar [baz]")
  equal(3, f.length)
  equal("foo", f[0].get('text'))
  ok( f[0].get('blank'))
  equal(" bar ",  f[1].get('text'))
  ok(!f[1].get('blank'))
  equal("baz", f[2].get('text'))
  ok( f[2].get('blank'))

test "CardFragment multiple hole", ->
  f = Blbr.CardFragment.split("1 [2] 3 [4] 5")
  equal(5, f.length)
  equal("1 ", f[0].get('text'))
  ok(!f[0].get('blank'))
  equal("2",  f[1].get('text'))
  ok( f[1].get('blank'))
  equal(" 3 ", f[2].get('text'))
  ok(!f[2].get('blank'))
  equal("4",  f[3].get('text'))
  ok( f[3].get('blank'))
  equal(" 5",  f[4].get('text'))
  ok(!f[4].get('blank'))

test "CardFragment blankStyle", ->
  f = Blbr.CardFragment.split("[123]")
  deepEqual({width: "3em"}, f[0].get('blankStyle'))

test "CardFragment isBlankSatisfied", ->
  f = Blbr.CardFragment.split("123 [456]")
  ok( f[0].isBlankSatisfied())
  ok(!f[1].isBlankSatisfied())
  f[1].set('filledText', "789")
  ok(!f[1].isBlankSatisfied())
  f[1].set('filledText', "456")
  ok( f[1].isBlankSatisfied())

test "CardFragment.parse should preverve the order", ->
  set = Blbr.CardFragment.parse("[foo] bar [baz]").toArray()
  equal("foo", set[0].get('text'))
  equal(" bar ", set[1].get('text'))
  equal("baz", set[2].get('text'))
