# lookit-data-processing

## What is this repo?

This is the code that allows an individual coder/researcher to download video from the Lookit S3 server to local storage, and which handles lookit-general information about datasets (e.g. whether or not an authorized person has confirmed the consent video), including the limited amount of info which is sent back to the Lookit videos (e.g. the personalized feedback that will be sent to families that participate.)

It's an instance of how you can use/access the lookit API, about which read more [here](http://readthedocs.org/projects/lookit/).

It also contains other useful scripts for dealing with video data from lookit, including VCode functions and example Python analysis  pipeline for a dataset.
(meaninless git test change)
## Installation (OSX directions)

0. Choose a location for the lookit-data-processing repo. This will *not* be the same disk location as the actual video, but it will be where you run the commands from to update the local storage and coding records from. It's good to pick where you really want to put these directories right now because some of the following steps will need to be rerun if you pick up either directory and move it elsewhere. Melissa thinks it's good to have the actual video download location somewhere separate from other project materials, since the PII lives there. Melissa's directory structure looks like this:

`RootDir/LookitVideo/` <- download location for video, where coding happens

`RootDir/Lookit/` <- other Lookit related materials live here

`RootDir/Lookit/lookit-data-processing` <- this repo

`RootDir/Lookit/Physics/` <- physics-specific files



1. Clone this repo at your chosen directory. You can fork it to keep track of your own changes on github if you want, and submit PRs to this repo.

2. Install pyenv (https://github.com/yyuu/pyenv)

3. Install python 2.7.x using pyenv, e.g. pyenv install 2.7.11

4. Install virtualenv: `[sudo] pip install virtualenv` (You may need to install pip first)

5. cd into the `scripts/` dir of the repo (where this very README file is located) & install requirements

	  virtualenv -p ~/.pyenv/versions/2.7.11/bin/python2.7 venv
	  source venv/bin/activate
	  pip install -r requirements.txt

NOTE that if at any point you decide to move the location of this repository, you'll need to rerun the above commands. Also, from now on, pay attention to whether or not you are in your `venv` when running commands! (Melissa had problems with libraries not 'staying installed', possibly due to lack of attention to virtualenv settings.)

6. Install ffmpeg (This takes a long time and is not inside the python virtual environment.) Lots of options are listed here, you should go ahead and install them all for now - with-freetype is definitely required; not sure of all others.

If you already have ffmpeg, run `brew uninstall ffmpeg` before doing the following (copy paste the whole thing into the terminal)

```
brew install ffmpeg \
--with-fdk-aac \
--with-fontconfig \
--with-freetype \
--with-frei0r \
--with-game-music-emu \
--with-libass \
--with-libbluray \
--with-libbs2b \
--with-libcaca \
--with-libgsm \
--with-libmodplug \
--with-libsoxr \
--with-libssh \
--with-libvidstab \
--with-libvorbis \
--with-libvpx \
--with-opencore-amr \
--with-openh264 \
--with-openjpeg \
--with-openssl \
--with-opus \
--with-rtmpdump \
--with-rubberband \
--with-sdl2 \
--with-snappy \
--with-speex \
--with-tesseract \
--with-theora \
--with-tools \
--with-two-lame \
--with-wavpack \
--with-webp \
--with-x265 \
--with-xz \
--with-zeromq \
--with-zimg
```

7. Install AWS command-line tools: see http://docs.aws.amazon.com/cli/latest/userguide/installing.html
    
    `sudo pip install awscli --ignore-installed six`

(The ignore-installed part prevents pip from fighting with some packages that now come preinstalled on macs)

## Configuration

### Obtain AWS keys, Configure AWS

To access video from the server, you'll need personal AWS keys. Ask Kim.

    `aws configure`

        enter keys (saved; can make new keys from AWS console)
        region: us-east-1
        output: json



### Generate OSF token

You will need to generate a personal access token on the OSF to run this script. Visit:

- [https://staging.osf.io/settings/tokens/](https://staging.osf.io/settings/tokens/)  _or_
- [https://osf.io/settings/tokens/](https://osf.io/settings/tokens/)

to do this.

![example](https://raw.githubusercontent.com/CenterForOpenScience/lookit/develop/scripts/pat-example.png)

**Make sure to save this token's value! You will not be able to retrieve it again.**

### Obtain Lookit token

You will also need a Lookit token, generated via the Lookit admin interface by an admin. Ask Kim.

### Obtain SendGrid key

To send email, you'll need a SendGrid key, generated by an admin. Ask Kim.

### Create a .env-prod

Create a new file named .env-prod in the current `scripts/` directory (where this README is). It should look like:

```
OSF_ACCESS_TOKEN=<your-osf-token>
LOOKIT_ACCESS_TOKEN=<your-lookit-token>

SENDGRID_KEY=<your-sendgrid-acct-key>

LOOKIT_URL=https://lookit.mit.edu

BASE_DIR= '/full/path/to/your/video/download/destination/'
VIDEO_DIR='video'
EXPORT_DIR='export'
SESSION_DIR='sessions'
DATA_DIR='data'
CODING_DIR='coding'
FFMPEG_PATH='/usr/local/bin/ffmpeg'
```

You'll need to fill in your keys, the `BASE_DIR` where you want all your data files and coding to live (full path, quoted, with leading and trailing slashes), and the path to ffmpeg (likewise). Note that the `BASE_DIR` is somewhere *other* than this (lookit-data-processing) repository location.

Each of the scripts accept an argument to point to a specific `.env` file (e.g. `.env-stage` or `.env-prod`), which you can use if you're working with both staging and production servers. For example:

```bash
python coding.py -config .env-stage
```

If you leave out the `-config .env-stage` option, the script will look for one named `.env-prod`

## Using the scripts

- To use the coding functions, first make sure you are in this directory (`scripts/`) by opening the Terminal program and typing cd [path to scripts], e.g.

cd /Volumes/NovelToy2/CurrentProjects/Lookit/scripts/

- `source venv/bin/activate` in order to get into the virtual environment; then can call some python scripts.

> python coding.py update --study physics
   get all the data!
> python coding.py fetchconsentsheet --coder Melissa --study physics 
   get yourself a spreadsheet you can read
   you may need to first add 'Melissa' to a coder list in codingSettings?
Then look at the human-readable csv and code consent, save the file
> python coding.py commitconsentsheet --coder Melissa --study physics
   saves your csv markings into the pickled-python data store under 'data'
> python coding.py update --study physics
   this is optional, it will run the update again and now that it knows about consent it'll process videos where consent is marked
> python coding.py sendfeedback --study physics 
   sends the stored feedback to the server



## TOUPDATE - Getting Help

(This command gives a skeleton file at the moment)

- For instructions on how to use coding.py, type
    python coding.py --help
from this directory.

### TOUPDATE - Setting up automation, on OSX:

- Edit the .plist file to use the correct path to updateLookit.sh (in this directory), to set the working directory to this directory, and to use .err/.out files in this directory. (Replace /Users/kms/lookitkim/scripts/ with this directory wherever you see it.)
- Copy the .plist file into $HOME/Library/LaunchAgents
- Make sure updateLookit.sh is executable: chmod +x updateLookit.sh (from this directory)
- Start the process: launchctl load ~/Library/LaunchAgents/com.lookit.update.plist
- You can stop using launchctl unload ~/Library/LaunchAgents/com.lookit.update.plist.
- You can see the output and any errors in autoSync.err and autoSync.out.

### TOUPDATE - Local data storage overview 

Warning: these may not be up-to-date. Would recommend loading the actual pickled files
and exploring a little to update.

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

Accounts: dict with user uuids as keys. [Add example value here]

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

Videos: keys are filenames (.flv/.mp4)
- shortName - subset of video name as used by sessions
- framerate
- duration
- expId
- sessionKey
- inBatches (key=batchId)
    - position
- mp4Path_[suffix] - relative, from SESSION_DIR. '' if not created yet.
- mp4Dur_[suffix] - duration of the mp4 in seconds; -1 if not created yet; 0 if could not be created.

email: keys are profileIds (e.g. kim2.zlkjs OR in new version uuids), values are lists of emails sent regarding that child's participation in this study.

Note: suffix is 'whole' or 'trimmed'; these fields are created when updating video data, although others could also be added.

## TOUPDATE - Optional Install - If you need to use matplotlib

7. (OPTIONAL) IF using matplotlib for anything (you don't need to except if you're making plots of looking time data in python!), make a separate virtualenv to do that because you'll need a framework version of python:

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

Now to run anything that requires matplotlib, you just use frameworkpython in place of python.
