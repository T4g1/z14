# z14

z14 [zia] is a bot designed to be an extended version of z03 [zoe] from the #inpres chan from maxux.net IRC.

## setup

Install requirements:
```
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
* .kt - Will say "Dans tes rêves @[user]"
* .o - Shows you what to do with your opinion
* .fr [title] [description] - Will add a feature request into z14's repository

## details

You need to configure the bot token in TOKEN

```
TOKEN=ifapme
```

* TOKEN: Secret TOKEN of the bot

### Auto role

New users added to the server will get the role defined in AUTO_ROLE

#### Config

```
AUTO_ROLE=Joueur
```

* AUTO_ROLE: Name of the role to be added by default

### Feature Request

Will send the feature request in the Git repository as an issue (just kidding, 
trolls the user thats all)

* .fr [title] [description]

### Self assigned roles

User can self assign pre-defined roles. They are defined in the env variable
ROLE_EMOJIS as a list of mapping emoji name to role formated as follows:
```
amongus,Among Us;csgo,Counter-Strike Global Offensive
```

The ID of the message users have to react to is given by ROLE_MESSAGE_ID

#### Config

```
ROLE_CHANNEL_ID=803356817533960213
ROLE_MESSAGE_ID=803361607652081734
ROLE_EMOJIS=amongus,Among Us;csgo,Counter-Strike Global Offensive
```

* ROLE_CHANNEL_ID: ID of the channel where the message is
* ROLE_MESSAGE_ID: ID of the message to react to
* ROLE_EMOJIS: `;` separated list of mapping of emoji's name to role's name (`,` separated list)

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

* MALABAR: Username and discriminator of the user to mute
* MALABAR_HISTORY_MAX_TIME: How many hours we keep for the history
* MALABAR_HISTORY_MAX_SIZE: Size of the history max before rejecting commands
* MALABAR_MUTE_TIME: Time to mute in seconds
* MALABAR_MUTE_ROLE: Role to assign so the user is muted

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
>.score avg

Display other statistics
>.score stats

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
SCORE_TRACKER_USER=[username]#[discriminator]
SCORE_TRACKER_TARGET=[username]#[discriminator]
SCORE_TRACKER_FIX_TIME=15
```

* SCORE_TRACKER_USER: Configure privilegied user for whom this command is available
* SCORE_TRACKER_TARGET: User for whom this command scores
* SCORE_TRACKER_FIX_TIME: Time during which we can fix the latest score command

## Resilience

The bot need to make sure the following is always true when re-started 
after a crash or update:
* All self-assigned roles are consistent with the emojis on the self 
assigned role message for every users
* All emojis not mapped are removed from the message for self-roles
* All users have at least the default role assigned to them
