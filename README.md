# z14

z14 [zia] is a bot designed to be an extended version of z03 [zoe] from the #inpres chan from maxux.net IRC.

## setup

Install requirements:
```
sudo apt install ffmpeg
pip3 install -r requirements.txt
```

Make a local copy of .env:
```
cp .env.sample .env
```

Setup values inside .env according to your environment and settings.

Run z14!
```
python3 z14.py
```

## features

* Reads configuration from .env file
* Assign a default role to any new user
* Assign roles to users based on reactions given to a specific message
* Parse commands

### commands

* .ping - pong
* .km - Will mute Malabar for 5 seconds
* .kp - Send a coucou to paglops
* .kt - Will say "Dans tes rêves @[user]"
* .o - Shows you what to do with your opinion
* .fr [title] [description] - Will add a feature request into z14's repository
* .sstats - Stats on score tracking
* .savg - Average of score tracking
* .score [score]/-[score] - Add the given score
* .fix [score]/-[score] - Remove latest score
* .ban - Plays the "Et on m'ban" sample
* .drum - Play the legendary ba dum tss sound effect
* .bp - Sends a picture to a specific channel

## details

You need the following configuration in `.env`:

```
TOKEN=ifapme
DB_PATH=sqlite:///[PATH]
```

* **TOKEN**: Secret TOKEN of the bot
* **DB_PATH**: Where will the DB be stored

### Auto role

New users added to the server will get the role defined in AUTO_ROLE

At all time, bot maker sure that:
* All users have at least the default role assigned to them

#### Config

```
AUTO_ROLE=Joueur
```

* **AUTO_ROLE**: Name of the role to be added by default

### Feature Request

Will send the feature request in the Git repository as an issue (just kidding, 
trolls the user thats all)

* .fr [title] [description]

### Self assigned roles

User can self assign pre-defined roles.

At all time, bot maker sure that:
* All self-assigned roles are consistent with the emojis on the self 
assigned role message for every users
* All emojis not mapped are removed from the message for self-roles


#### Config

```
ROLE_CHANNEL_ID=803356817533960213
ROLE_MESSAGE_ID=803361607652081734
ROLE_EMOJIS=amongus,Among Us;csgo,Counter-Strike Global Offensive
```

* **ROLE_CHANNEL_ID**: ID of the channel where the message is
* **ROLE_MESSAGE_ID**: ID of the message to react to
* **ROLE_EMOJIS**: `;` separated list of mapping of emoji's name to role's name (`,` separated list)

### Kick Malabar

Based on the original km for kick malabar

* Can not be used more than 3 times a day
* Duration of mute is hardcoded to 5 seconds
* Keep track of how many times the command was used in the last 24hours
* How much time Malabar spent muted in the last 24hours
* Mute Malabar for an arbitrary amount of time
* Unmute Malabar when the timer expires
* Refuses any subsequent km while Malabar is muted by the command
* Detects if Malabar is in a vocal channel

#### Config

```
MALABAR=Jonh#0538
MALABAR_HISTORY_MAX_TIME=1
MALABAR_HISTORY_MAX_SIZE=10
MALABAR_MUTE_TIME=5
MALABAR_MUTE_ROLE=Muted
```

* **MALABAR**: Username and discriminator of the user to mute
* **MALABAR_HISTORY_MAX_TIME**: How many hours we keep for the history
* **MALABAR_HISTORY_MAX_SIZE**: Size of the history max before rejecting commands
* **MALABAR_MUTE_TIME**: Time to mute in seconds
* **MALABAR_MUTE_ROLE**: Role to assign so the user is muted

### Kick Paglops

Embeds an horrible pirate where invoked

* kp will send a pirate into the channel

#### Config

```
PAGLOPS_URL=image.jpg
```

* PAGLOPS_URL: Url of the pirate picture

### Kick T4g1

Whoever invokes it will be flagged as a dangerous criminal

* kt will give a nice message to whoever invoked it
* z14 will try to intimidate whoever sent it

### Opinion

Send a picture of what to do with your opinion.

#### Config

```
OPINION_URL=image.jpg
```

* OPINION_URL: Url of the picture to embed

### Score Tracker

Track T4g1 scores on jokes, provide its current average score as well as useful statistics.

Add score
>.score +x

Remove score
>.score -x

Display score average
>.savg

Display other statistics
>.sstats

Only SCORE_TRACKER_USER should be able to use the feature.

#### Scoring
**Add new scores**
The score is calculated over 10 points, with -10 being the lowest and 10 the highest.
After each joke, the score is input with 
> .score x

where x = score sur [-10;10]

**Correct score**
In case of error, the scores which have been input in the last SCORE_TRACKER_FIX_TIME can be removed.
> .fix x

The functionality must check x against the latest input value & remove only one which matches.

#### Statistics
**Current average**
The current average is calculated by SOMME(score)/COUNT(score)

**Other statistics**
- Trend over the past week / month / year
- Highest / lowest score - All time
- Highest / lowest score - Last month
- Highest / lowest score - Last week

#### Config

```
SCORE_TRACKER_PATH=[filepath]
SCORE_TRACKER_USER=[username]#[discriminator]
SCORE_TRACKER_TARGET=[username]#[discriminator]
SCORE_TRACKER_FIX_TIME=15
```

* **SCORE_TRACKER_PATH**: Where to save data. defaults to `score_tracker.dat`
* **SCORE_TRACKER_USER**: Configure privilegied user for whom this command is available
* **SCORE_TRACKER_TARGET**: User for whom this command scores
* **SCORE_TRACKER_FIX_TIME**: Time during which we can fix the latest score command

### Sound effects

Joins the user that invokes it in vocal and plays a sound effect

* .ban - Do the "Et on m'ban" sound effect
* .drum - Do the "Ba dum tss" sound effect

#### Dependancy

* If the module Score Tracker is loaded, will play a drum effect when T4g1 got
a bad score

#### Config

```
SFX_BAN_URL=[ban URL]
SFX_DRUM_URL=[drum URL]
```

* **SFX_BAN_URL**: Ban sound effect location
* **SFX_DRUM_URL**: Drum sound effect location

### Statistics

Provides various stats

* .stats - Provides global stats
* .suser [pseudo] - Provides stats for a specific user
* .stop - Provides leaderboards

### Popof

Sends a picture to a specific channel

#### Config

```
POPOF_URL=[URL]
POPOF_CHANNEL=[ID of the chan where it can be used]
```

* **POPOF_URL**: What image to send
* **POPOF_CHANNEL**: Where to send the image

## Dev

To make a succesfull pull request follow this workflow:

* Fork the project
* Describes the feature in an issue on the z14 repository
* When approved, create a branch named `z14-333_title` on your fork (with 333 
being the issue number and title wathever you want related to the issue)
* Do your dev
* Create a pull request closing the issue you created 

### z14.py

* Handle modules loading and self testing.
* Provides basic publish/subscribe design pattern to reduce inter-modules 
dependancy

#### Adding a module

Into your module, you have to add this method outside your module class:
```
def setup(bot):
    bot.add_cog(ScoreTracker(bot))
```

Then in `z14/py`, add your module to the list:
```py
self.modules = [
    'modules.auto_role',
    'modules.feature_request',
    ...
]
```

#### Testing

Your module should define the following method:
```py
def test(self):
    # Do your testing here
    assert not os.getenv("SCORE_TRACKER_USER") is None, \
        "SCORE_TRACKER_USER is not defined"

    try:
        time = int(os.getenv("SCORE_TRACKER_FIX_TIME"))
    except Exception as e:
        self.fail("SCORE_TRACKER_FIX_TIME is not a proper integer")
```

#### Publish/Subscribe design pattern

**Publishing to a topic**

In your custom module:
```py
await self.bot.publish(ctx, "score_tracker.scored", score)
```

You should give the current commands.Context, the topic name and some 
value (optionnal)

**Listening to a topic**

In your custom module on_ready:
```py
@commands.Cog.listener()
async def on_ready(self):
    await self.bot.subscribe("score_tracker.scored", self)
```

You should give the topic name and who is listening (self)

Then you need to define the callback as follows:
```py
async def on_topic_published(self, ctx, topic, value):
    # Change to put your code here
    pass
```

### Modules

* Every module you add should go in that folder
