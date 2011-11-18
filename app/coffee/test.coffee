
class FakingAjaxSend
  constructor: ->
    @sent_reqs = []
    @original = Batman.Request::send
    self = this
    Batman.Request::send = (data) ->
      console.log("Send:", this, data)
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
    console.log(Blbr.Card)
    faking.respond(200, { "r/me/cards": ["id": "foo"] })
    equal(console.log(ret.reduce()), "foo")
    start()
