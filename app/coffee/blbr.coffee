
hello = (msg) -> alert(msg)

class BlBr extends Batman.App
  @global yes
  @root 'todos#index'

class BlBr.Card extends Batman.Model
  @global yes
  @persist Batman.RestStorage
  @storageKey: 'r/me/card'
  @encode 'owner', 'face', 'back'

class BlBr.CardController extends Batman.Controller
  emptyTodo: null

  index: ->
  create: =>

