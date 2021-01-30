import os
import pickle
DEFAULT_PATH = "kick_tracker_malabar.dat"


class MalabarKickTracker:
    def __init__(self):
        self.history = {}
        self.filename = os.getenv("KICK_TRACKER_PATH", default=DEFAULT_PATH)
        self.load()

    def load(self):
        """ Load persisted data from disk
        """
        try:
            with open(self.filename, 'rb') as file:
                self.history = pickle.load(file)
        except FileNotFoundError:
            pass

    def persist(self):
        """ Persist data on disk
        """
        with open(self.filename, 'wb') as file:
            pickle.dump(self.history, file)

    async def inc(self, ctx):
        db = self.history
        sender = ctx.author.id
        if sender in db:
            db[sender]['xp'] += 1
            if db[sender]['xp'] >= db[sender]['next']:
                db[sender]['xp'] = 0
                db[sender]['lvl'] += 1
                db[sender]['next'] += int(db[sender]['next'] * .4)
        else:
            db[sender] = {
                'xp': 1,
                'lvl': 0,
                'next': 10,
            }

        self.history = db
        self.persist()
        await ctx.send('{} xp, {} lvl, {} next'.format(
            db[sender]['xp'],
            db[sender]['lvl'],
            db[sender]['next'])
        )

    def get_level(self, ctx):
        db = self.history
        sender = ctx.author.id
        if sender in db:
            return db[sender]['lvl']
        return 0
