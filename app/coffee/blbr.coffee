

class Blbr extends Batman.App
  @global yes
  @root 'cards#index'

class JsonRestStorage extends Batman.RestStorage
  serializeAsForm: false

class Blbr.CardFragment extends Batman.Object
  constructor: (text, open) ->
     super(text: text, open: open)
  @_parse_append: (str, a) ->
    if m = str.match(/([^\[]*)\[([^\]]*)\](.*)/)
      a.push(new Blbr.CardFragment(m[1], true)) if m[1].length
      a.push(new Blbr.CardFragment(m[2], false))
      @_parse_append(m[3], a)
    else
      a.push(new Blbr.CardFragment(str, true)) if str.length
    a
  @split: (str) ->
    @_parse_append(str, [])

class Blbr.Card extends Batman.Model
  @storageKey: 'r/me/card'
  @persist JsonRestStorage
  @encode 'owner', 'face', 'back', 'next_round', 'pass_count', 'fail_count', 'succession'
  face: ''
  back: ''

  constructor: ->
    super
    @observe 'face', => @set('face_fragments', Blbr.CardFragment.split(@get('face')))

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
  score_as_pass: ->
    @set('pass_count', @get('pass_count') + 1)
    @set('succession', @get('succession') + 1)
    @set('next_round', @get('last_round') + @get('succession'))
  pass: ->
    @score_as_pass()
    @save()
  score_as_fail: ->
    @set('fail_count', @get('fail_count') + 1)
    @set('succession', 0)
  fail: ->
    @score_as_fail()
    @save()

  @accessor 'face_fragments'
    get: (key) ->
      @face_fragments ||= new Batman.Set()
    set: (key, val) ->
      (@face_fragments ||= new Batman.Set()).clear()
      @face_fragments.merge(val)

#  @accessor 'back_fragments'
#    get: => Blbr.CardFragment.split(@get('back'))


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

