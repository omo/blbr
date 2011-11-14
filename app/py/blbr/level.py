
import blbr.user
import blbr.restics as restics
import blbr.wsgis as wsgis

from google.appengine.ext import db

class LevelRepo(restics.Repo):
    url_pattern = '/r/([^/]+)/level'
    item_namespace = 'r/me/level'
    
    def __init__(self):
        restics.Repo.__init__(self)
        self.parent = blbr.user.UserRepo()

    @wsgis.login_required
    def get(self, positionals):
        if not self.has_full_positional(positionals):
            logging.info(self.__class__.__name__, ".get: Missing ID for GET")
            return None
        owner = self.parent.find_by_keylike(positionals[-1])
        if not owner:
            logging.info(self.__class__.__name__, ".get: No owner")
            return None
        return owner.level

    @wsgis.login_required
    def put(self, positionals, bag):
        if not self.has_full_positional(positionals):
            logging.info(self.__class__.__name__, ".put: Missing ID for PUT")
            return None
        owner = self.parent.find_by_keylike(positionals[0])
        if not owner:
            logging.info(self.__class__.__name__, ".put: No owner")
            return None
        try:
            owner.put_level(owner.level.updated_by_bag(bag))
            return owner.level
        except db.BadValueError as e:
            logging.info("CardRepo.put: BadValueError %s", e)
            return None



LevelController = restics.controller_for(LevelRepo)
