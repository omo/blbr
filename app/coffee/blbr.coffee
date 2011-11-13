
class Blbr extends Batman.App
  @global yes
  @root 'cards#index'

class JsonRestStorage extends Batman.RestStorage
  serializeAsForm: false

class Blbr.Card extends Batman.Model
  @persist JsonRestStorage
  @storageKey: 'r/me/card'
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

class Blbr.CardsController extends Batman.Controller
  index: ->
    @set 'emptyCard', new Blbr.Card()
    @render no
  create: =>
    @emptyCard.save (error, record) =>
      throw error if error
      @set 'emptyCard', new Blbr.Card()
