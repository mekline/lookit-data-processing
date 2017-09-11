# Steps to run

## Configuration

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
OSF_ACCESS_TOKEN=<your-staging-access-token>
JAMDB_URL=https://staging-metadata.osf.io
JAMDB_NAMESPACE=experimenter
```

or

```
OSF_ACCESS_TOKEN=<your-access-token>
JAMDB_URL=https://metadata.osf.io
JAMDB_NAMESPACE=lookit
```

Each the scripts accept an argument to point to a specific .env file (e.g. '.env-stage' or '.env-prod'). For example:

```bash
python client.py -c .env-stage
```

## Install

1. Create a virtualenvironment using a python 2.7.X executable
2. `pip install -r requirements.txt`

# Included Code

## client.py

This file mostly contains some examples and utilites for interacting with the JamDB API.

## sendgrid_client.py

This file gives some examples of using the sendgrid Python client to interact with SendGrid's suppression groups and send emails to users. 
You can add the`SENDGRID_KEY` setting to your .env to avoid having to pass an `apikey` argument to the sendgrid_client.SendGrid constructor.

## email_migrated_users.py

This script fetches all of the users with a non-null value of `migratedFrom` attribute and issues a password reset request for them. Usage:
`python email_migrated_users.py -DR true|false -D true|false -V 0|1|2`

where:

	*`-DR` specifies whether this is a 'dry-run' or not. Setting this flag true (default) will make the script only log who password requests are sent to (not actually sending emails). Set this false to actaully send emails.
	
	*`-D` specifies whether or not to use debug mode. Debug mode means if an unexpected server response is seen an IPDB shell is opened to inspect the program state.
	
	*`-V` specifies verbositiy. Use integers 0-2 to pick a logging level (0=NOTSET, 1=INFO, 2=DEBUG)
	

scripts: coding workflow
(https://github.com/CenterForOpenScience/lookit/tree/develop/scripts)

## coding.py

To use the coding functions, first navigate to this directory (scripts) by opening the
Terminal program and typing cd [path to scripts], e.g.
cd /Volumes/NovelToy2/CurrentProjects/Lookit/scripts/

For instructions on how to use coding.py, type
	python coding.py --help
from this directory.

### Initial installation so client.py can work:

- Get token
- Install pyenv (https://github.com/yyuu/pyenv), due to issues with regular python. Follow all instructions there, using homebrew. (Kim saw error "The Python zlib extension was not compiled. Missing the zlib? Please consult to the Wiki page to fix the problem. https://github.com/yyuu/pyenv/wiki/Common-build-problems. Solution: Needed to use `CFLAGS="-I$(xcrun --show-sdk-path)/usr/include" pyenv install -v 2.7.11` to install.)

- Install virtualenv: `[sudo] pip install virtualenv`

- Create virtualenv in scripts dir

	  virtualenv -p ~/.pyenv/versions/2.7.11/bin/python2.7 venv
	  source venv/bin/activate
	  pip install -r requirements.txt

- For framework version, separately:
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


### To start using:

- Create a file .env in this directory like this, substituting in a reasonable base location for the video/batch/session/data/coding directories.

```
	OSF_ACCESS_TOKEN=<OSF ACCESS TOKEN HERE!>

	OSF_CLIENT_ID=<application_client_id>
	OSF_SCOPE=osf.users.all_read
	OSF_URL=https://staging-accounts.osf.io

	WOWZA_PHP='{}'
	WOWZA_ASP='{}'

	JAMDB_URL=https://staging-metadata.osf.io
	JAMDB_NAMESPACE=experimenter

	VIDEO_DIR='/Users/kms/lookitcoding/video'
	BATCH_DIR='/Users/kms/lookitcoding/batches'
	SESSION_DIR='/Users/kms/lookitcoding/sessions'
	DATA_DIR='/Users/kms/lookitcoding/data'
	CODING_DIR='/Users/kms/lookitcoding/coding'
	FFMPEG_PATH='/usr/local/bin/ffmpeg'
```

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


### Setting up for data analysis if you want to use ipython

- Install MacPorts.

- Outside of the venv, set up numpy/scipy/matplotlib/ipython stack:

    `sudo port install py27-numpy py27-scipy py27-matplotlib py27-ipython +notebook py27-pandas py27-sympy py27-nose`

    (follow additional warnings/instructions during install)

- Get pip for the version of python used by ipython:
download get-pip.py from https://packaging.python.org/installing/
`sudo python2.7 get-pip.py`

- Install packages on this version as needed with this pip:
sudo python2.7 -m pip install requests
sudo python2.7 -m pip install -U python-dotenv


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

Accounts: dict with usernames as keys; example of value:

```json

u'samchrisnger': {	 
    u'attributes': {	
        u'demographicsAdditionalComments': None,
		u'demographicsAge': None,
        u'demographicsAnnualIncome': None,
        u'demographicsCanScheduleAnAppointment': None,
        u'demographicsEducationLevel': None,
        u'demographicsGender': None,
        u'demographicsLanguagesSpokenAtHome': u'',
        u'demographicsNumberOfBooks': None,
        u'demographicsNumberOfChildren': u'0',
        u'demographicsNumberOfGuardians': None,
        u'demographicsNumberOfGuardiansExplanation': None,
        u'demographicsRaceIdentification': None,
        u'demographicsSpouseEducationLevel': None,
        u'demographicsWillingToBeContactedForSimilarStudies': None,
        u'email': u's.chrisinger@gmail.com',
        u'emailPreferencesNewStudies': False,
        u'emailPreferencesResearcherQuestions': False,
        u'emailPreferencesResultsPublished': False,
        u'mustResetPassword': False,
        u'password': u'$2b$12$eEGfB9n.ToKtSDnEVBjkeurXSt/Lj308jHFguNBM3QuhZa1.la1Ga',
        u'profiles': [	 {	 u'ageAtBirth': u'Over 24 Weeks',
                             u'birthday': u'2015-11-13T05:00:00.000Z',
                             u'firstName': u'Sam',
                             u'gender': u'Male',
                             u'profileId': u'samchrisnger.pnazo'}],
        u'username': u'samchrisnger'
     },
     u'id': u'experimenter.accounts.samchrisnger',
     u'meta': {	  u'created-by': u'jam-experimenter:accounts-samchrisnger',
                  u'created-on': u'2016-03-17T15:21:30.792581',
                  u'modified-by': u'jam-experimenter:accounts-samchrisnger',
                  u'modified-on': u'2016-03-17T15:36:36.355045',
                  u'permissions': u'ADMIN'
     }
    }

```


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



