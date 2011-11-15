
class Blbr extends Batman.App
  @global yes
  @root 'cards#index'

class JsonRestStorage extends Batman.RestStorage
  serializeAsForm: false

class Blbr.Card extends Batman.Model
  @storageKey: 'r/me/card'
  @persist JsonRestStorage
  @encode 'owner', 'face', 'back'
  face: ''
  back: ''

  edit: (target) ->
    @set 'editing', true
    $(target).find('input').first().select()
  cancel: (target, evt) ->
    evt.stopPropagation() if evt
    # XXX: check dirtiness
    @load => @set 'editing', false
  save: ->
    super =>
      @set 'editing', false

class Blbr.Level extends Batman.Model
  @storageKey: 'r/me/level'
  @persist JsonRestStorage
  @encode 'round'

  @placeholderKey: 'latest'
  @url: (options) -> "/#{@storageKey}"
  @classAccessor 'mime', ->
    console.log("mime getter")
    # XXX: The guard condition should be a method.
    @find(@placeholderKey, (err, records) -> console.log(err, records)) # if @::hasStorage() and @classState() not in ['loaded', 'loading']


class Blbr.CardsController extends Batman.Controller
  index: ->
    @set 'emptyCard', new Blbr.Card()
    @render no
  create: =>
    @emptyCard.save (error, record) =>
      throw error if error
      @set 'emptyCard', new Blbr.Card()
