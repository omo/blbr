

class Blbr extends Batman.App
  @global yes
  @root 'cards#index'

class JsonRestStorage extends Batman.RestStorage
  serializeAsForm: false

class Blbr.CardFragment extends Batman.Object
  constructor: (text, blank) ->
     super(text: text, filledText: "", blank: blank)
  @_parse_append: (str, a) ->
    if m = str.match(/([^\[]*)\[([^\]]*)\](.*)/)
      a.push(new Blbr.CardFragment(m[1], false)) if m[1].length
      a.push(new Blbr.CardFragment(m[2], true))
      @_parse_append(m[3], a)
    else
      a.push(new Blbr.CardFragment(str, false)) if str.length
    a
  @split: (str) ->
    @_parse_append(str, [])
  @parse: (str) ->
    set = new Batman.Set()
    @split(str).forEach((e) => set.add(e))
    set
  # XXX this kind of presentation stuff should be held somewhere else.
  @accessor 'blankStyle', -> { width: "#{@get('text').length}em" }

  isBlankSatisfied: ->
    (not @blank) or (@text is @filledText)
  fill: (text) -> @set('filledText', text)

class Blbr.Card extends Batman.Model
  @storageKey: 'r/me/card'
  @persist JsonRestStorage
  @encode 'owner', 'face', 'back', 'next_round', 'pass_count', 'fail_count', 'succession'
  face: ''
  back: ''

  constructor: ->
    super
    @observe 'face', (value) =>
      @set('face_fragments', Blbr.CardFragment.parse(value))
    @observe 'back', (value) =>
      @set('back_fragments', Blbr.CardFragment.parse(value))

  @classAccessor 'round'
    get: =>
      @load(sort: 'round')
      @get('loaded')
  # XXX: doesn't use 'all' here to force @load() regardless of @classState.
  @classAccessor 'freshAll'
    get: =>
      @load()
      @get('loaded')
  edit: (target) ->
    @set 'editing', true
    $(target).find('input').first().select()
  cancel: (target, evt) ->
    evt.stopPropagation() if evt
    # TODO(omo): check dirtiness to skip redundant requests.
    @load => @set 'editing', false
  save: ->
    super =>
      @set 'editing', false
  scoreAsPass: ->
    @set('pass_count', @get('pass_count') + 1)
    @set('succession', @get('succession') + 1)
    @set('next_round', @get('last_round') + @get('succession'))
  pass: ->
    @scoreAsPass()
    @save()
  scoreAsFail: ->
    @set('fail_count', @get('fail_count') + 1)
    @set('succession', 0)
  fail: ->
    @scoreAsFail()
    @save()
  doJudge: ->
    @unsatisfied = @face_fragments.filter((f) -> !f.isBlankSatisfied())
    @unsatisfied = null if 0 == @unsatisfied.length
    @unsatisfied
  judge: ->
    @doJudge()
    @set('judged', true)
    @set('failing', @unsatisfied isnt null)
    @set('passing', @unsatisfied is   null)

    if @failing
      @fail()
    else
      @pass()

  _resetJudge: ->
    @set('judged', false)
    @set('failing', false)
    @set('passing', false)
  retry: ->
    @_resetJudge()
  proceed: ->
    @_resetJudge()

  @setReplacyAndGetLazilyFor: (name) ->
    get: (key) ->
      @[name] ||= new Batman.Set()
    set: (key, val) ->
      (@[name] ||= new Batman.Set()).replace(val)

  @accessor 'face_fragments', @setReplacyAndGetLazilyFor('face_fragments')
  @accessor 'back_fragments', @setReplacyAndGetLazilyFor('back_fragments')

class Blbr.Level extends Batman.Model
  @storageKey: 'r/me/level'
  @persist JsonRestStorage
  @encode 'round'

  @placeholderKey: 'latest'
  @url: (options) -> "/#{@storageKey}"
  @classAccessor 'mime', ->
    @find(@placeholderKey, (err, records) -> console.log(err, records) if err)  # if @::hasStorage() and @classState() not in ['loaded', 'loading']


class Blbr.CardsController extends Batman.Controller
  index: ->
    @set 'emptyCard', new Blbr.Card()
    @render no
  create: =>
    @emptyCard.save (error, record) =>
      throw error if error
      @set 'emptyCard', new Blbr.Card()

