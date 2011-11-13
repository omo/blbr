
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

class Blbr.CardsController extends Batman.Controller
  index: ->
    @set 'emptyCard', new Blbr.Card()
    @render no

  create: =>
    @emptyCard.save (error, record) =>
      throw error if error
      @set 'emptyCard', new Blbr.Card()

