# Steps to run

## Configuration

### TODO: document new config steps.

### Generate a token
You will need to generate a personal access token on the OSF to run this script. Visit:

- [https://staging.osf.io/settings/tokens/](https://staging.osf.io/settings/tokens/)  _or_
- [https://osf.io/settings/tokens/](https://osf.io/settings/tokens/)

to do this.

![example](https://raw.githubusercontent.com/CenterForOpenScience/lookit/develop/scripts/pat-example.png)

**Make sure to save this token's value! You will not be able to retrieve it again.**

### Create a .env

Create a new file name .env in this directory. It should look like:

```
OSF_ACCESS_TOKEN=<your-osf-token>
LOOKIT_ACCESS_TOKEN=<your-lookit-token>

OSF_CLIENT_ID=<application_client_id>
OSF_SCOPE=osf.users.all_read
OSF_URL=https://accounts.osf.io

SENDGRID_KEY=<your-sendgrid-acct-key>

WOWZA_PHP='{"minRecordTime":1,"showMenu":"false","showTimer":"false","enableBlinkingRec":1,"skipInitialScreen":1,"recordAgain":"false","showSoundBar":"false","hideDeviceSettingsButtons":1,"connectionstring":"rtmps://lookit-streaming.mit.edu/hdfvr/_lookit_"}'
WOWZA_ASP='{"showMenu":"false","loopbackMic":"true","skipInitialScreen":1,"showSoundBar":"false","snapshotEnable":"false"}'

LOOKIT_URL=https://lookit.mit.edu

BASE_DIR='/Users/kms/lookitcodingmultilab/'
VIDEO_DIR='video'
EXPORT_DIR='export'
SESSION_DIR='sessions'
DATA_DIR='data'
CODING_DIR='coding'
FFMPEG_PATH='/usr/local/bin/ffmpeg'
```

Each the scripts accept an argument to point to a specific .env file (e.g. '.env-stage' or '.env-prod'). For example:

```bash
python coding.py -config .env-stage
```

## Install

1. Create a virtualenvironment using a python 2.7.X executable
2. `pip install -r requirements.txt`

# Included Code

## coding.py

To use the coding functions, first navigate to this directory (scripts) by opening the
Terminal program and typing cd [path to scripts], e.g.
cd /Volumes/NovelToy2/CurrentProjects/Lookit/scripts/

For instructions on how to use coding.py, type
	python coding.py --help
from this directory.

### Installation

- Get token

- Install pyenv (https://github.com/yyuu/pyenv)

- Install python 2.7.x using pyenv, e.g. pyenv install 2.7.11

- Install virtualenv: `[sudo] pip install virtualenv`

- Create virtualenv in scripts dir

	  virtualenv -p ~/.pyenv/versions/2.7.11/bin/python2.7 venv
	  source venv/bin/activate
	  pip install -r requirements.txt

- If using matplotlib, make a separate virtualenv:

```
	brew install python --framework
	virtualenv -p /usr/local/Cellar/python/2.7.12_1/bin/python2.7 fwenv
```

	from http://matplotlib.org/faq/virtualenv_faq.html:

	> The best known workaround, borrowed from the WX wiki, is to use the non virtualenv python along with the PYTHONHOME environment variable. This can be implemented in a script as below. To use this modify PYVER and PATHTOPYTHON and put the script in the virtualenv bin directory i.e. `PATHTOVENV/bin/frameworkpython`
	
```
		#!/bin/bash

		# what real Python executable to use
		PYVER=2.7
		PATHTOPYTHON=/usr/local/Cellar/python/2.7.12_1/bin/
		PYTHON=${PATHTOPYTHON}python${PYVER}

		# find the root of the virtualenv, it should be the parent of the dir this script is in
		ENV=`$PYTHON -c "import os; print(os.path.abspath(os.path.join(os.path.dirname(\"$0\"), '..')))"`

		# now run Python with the virtualenv set as Python's HOME
		export PYTHONHOME=$ENV
		exec $PYTHON "$@"
```

	With this in place you can run frameworkpython to get an interactive framework build within the virtualenv. To run a script you can do frameworkpython test.py where test.py is a script that requires a framework build. To run an interactive IPython session with the framework build within the virtual environment you can do `frameworkpython -m IPython`

```
source fwenv/bin/activate
pip install -r requirements.txt
pip install matplotlib
pip install scipy
```

Now to run anything that requires matplotlib, use frameworkpython in place of python.

- Install AWS command-line tools: see    http://docs.aws.amazon.com/cli/latest/userguide/installing.html
    
    `sudo pip install awscli`

    `aws configure`

        enter keys (saved; can make new keys from AWS console)
        region: us-east-1

- `source venv/bin/activate` in order to get into the virtual environment; then can call python scripts.

### Setting up automation, on OSX:

- Edit the .plist file to use the correct path to updateLookit.sh (in this directory), to set the working directory to this directory, and to use .err/.out files in this directory. (Replace /Users/kms/lookitkim/scripts/ with this directory wherever you see it.)
- Copy the .plist file into $HOME/Library/LaunchAgents
- Make sure updateLookit.sh is executable: chmod +x updateLookit.sh (from this directory)
- Start the process: launchctl load ~/Library/LaunchAgents/com.lookit.update.plist
- You can stop using launchctl unload ~/Library/LaunchAgents/com.lookit.update.plist.
- You can see the output and any errors in autoSync.err and autoSync.out.

- To start also sending emails, will need to add the line
	python reminder_emails.py --study physics --emails all
	to updateLookit.sh

- (I have also now set up a weekly job that just sends the feedback-only emails as needed)


### Local data storage overview 


.env file defines:
- Video directory (where raw videos live)
- Batch video directory (where batched videos live)
- Coding directory (where human-readable spreadsheets live)
- Coder names
- Data directory (everything below is data)

Coding: dict with sessionKey as keys, values are dicts with structure:
- Consent
- coderComments
    coderName
- videosExpected: list of video filenames expected, based on session data
- videosFound: list of video filenames actually found; list of lists corresponding to videosExpected

Accounts: dict with user uuids as keys; example of value:

Sessions: array of dicts each with the following structure (directly from server):
- Attributes
    - Feedback
    - Sequence
    - expData
        - [frame-name]
            - eventTimings
                - eventType (nextFrame, ...)
                - timestamp
            - ...
    - experimentId
    - profileId (username.child)
    - conditions
    - completed
    - hasReadFeedback
- meta
    - created-on
- id (=sessionKey)

Batch: keys are unique batch IDs
- batchFile: filename of batch
- videos: ordered list of (sessionId, videoname) pairs
- codedBy: set of coder names

Videos: keys are filenames (.flv)
- shortName - subset of video name as used by sessions
- framerate
- duration
- expId
- sessionKey
- inBatches (key=batchId)
    - position
- mp4Path_[suffix] - relative, from SESSION_DIR. '' if not created yet.
- mp4Dur_[suffix] - duration of the mp4 in seconds; -1 if not created yet; 0 if could not be created.

email: keys are profileIds (e.g. kim2.zlkjs), values are lists of emails sent regarding that child's participation in this study.

Note: suffix is 'whole' or 'trimmed'; these fields are created when updating video data, although others could also be added.
