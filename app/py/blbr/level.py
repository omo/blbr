
import logging

import blbr.user
import blbr.restics as restics
import blbr.wsgis as wsgis

from google.appengine.ext import db

class LevelRepo(restics.Repo):
    item_url_pattern = '/r/<user_id:[^/]+>/level/latest'
    item_namespace = 'r/me/level'
    
    def __init__(self):
        restics.Repo.__init__(self)
        self.parent = blbr.user.UserRepo()

    @wsgis.login_required
    def get(self, params):
        owner = self.parent.get(params)
        if not owner:
            logging.info(self.__class__.__name__, ".get: No owner")
            return None
        return owner.level

    @wsgis.login_required
    def put(self, params, bag):
        owner = self.parent.get(params)
        if not owner:
            logging.info(self.__class__.__name__, ".put: No owner")
            return None
        try:
            owner.put_level(owner.level.updated_by_bag(bag))
            return owner.level
        except db.BadValueError as e:
            logging.info("CardRepo.put: BadValueError %s", e)
            return None


LevelController = restics.item_controller_for(LevelRepo)
