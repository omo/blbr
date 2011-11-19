
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

asyncTest "Instantiate Card model", ->
  faking = new FakingAjaxSend()
  ret = Blbr.Card.get('all')
  setTimeout ->
    equal(1, faking.sent_reqs.length)
    faking.respond(200, { "r/me/cards": ["id": "foo"] })
    equal(ret.reduce().get("id"), "foo")
    start()

make_fixture_card = ->
  card = new Blbr.Card(next_round: 10, pass_count: 1, fail_count: 2, succession: 3)
  card.set('last_round', 20)
  card

test "Card.score_as_pass", ->
  card = make_fixture_card()
  card.score_as_pass()
  equal(card.get("next_round"), 24)
  equal(card.get("pass_count"),  2)
  equal(card.get("fail_count"),  2)
  equal(card.get("succession"),  4)

test "Card.score_as_fail", ->
  card = make_fixture_card()
  card.score_as_fail()
  equal(card.get("next_round"), 10)
  equal(card.get("pass_count"),  1)
  equal(card.get("fail_count"),  3)
  equal(card.get("succession"),  0)
