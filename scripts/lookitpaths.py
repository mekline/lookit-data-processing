import os
from utils import make_sure_path_exists
import conf

#OSF_ACCESS_TOKEN = os.environ.get('OSF_ACCESS_TOKEN')
#SENDGRID_KEY = os.environ.get('SENDGRID_KEY')
CODERS = eval(os.environ['CODERS'])
BASE_DIR=os.environ.get("BASE_DIR")
VIDEO_DIR = os.path.join(BASE_DIR, os.environ.get("VIDEO_DIR"))
BATCH_DIR = os.path.join(BASE_DIR, os.environ.get("BATCH_DIR"))
DATA_DIR = os.path.join(BASE_DIR, os.environ.get("DATA_DIR"))
CODING_DIR = os.path.join(BASE_DIR, os.environ.get("CODING_DIR"))
SESSION_DIR = os.path.join(BASE_DIR, os.environ.get("SESSION_DIR"))
FIG_DIR = os.path.join(CODING_DIR, 'figs')
FFMPEG = os.environ.get("FFMPEG_PATH")
FFPROBE = os.path.join(os.path.split(FFMPEG)[0], 'ffprobe')

make_sure_path_exists(VIDEO_DIR)
make_sure_path_exists(BATCH_DIR)
make_sure_path_exists(DATA_DIR)
make_sure_path_exists(CODING_DIR)
make_sure_path_exists(SESSION_DIR)

VIDEO_FILENAME = os.path.join(DATA_DIR, 'video_data.bin')
ACCOUNT_FILENAME = os.path.join(DATA_DIR, 'accounts' + conf.VERSION + '.bin')

studyNicknames = {'physics': '583c892ec0d9d70082123d94',
                  'test': '57adc3373de08a003fb12aad',
                  'pilot': '57dae6f73de08a0056fb4165',
                  'prodpilot':'57bc591dc0d9d70055f775db'}

def session_filename(expId):
    '''Return full path to the session data filename for experiment expId'''
    return os.path.join(DATA_DIR, 'session_data_' + expId + '.bin')

def email_filename(expId):
    '''Return full path to the session data filename for experiment expId'''
    return os.path.join(DATA_DIR, 'email_data_' + expId + conf.VERSION + '.bin')

def coding_filename(expId):
    '''Return full path to the coding data filename for experiment expId'''
    return os.path.join(DATA_DIR, 'coding_data_' + expId + '.bin')

def batch_filename(expId):
    '''Return full path to the batch data filename for experiment expId'''
    return os.path.join(DATA_DIR, 'batch_data_' +  expId + '.bin')

def vcode_batchfilename(batchFilename, coderName):
    '''Return full path to expected VCode file for a given batch & coder'''
    batchStub, ext = os.path.splitext(batchFilename)
    return os.path.join(CODING_DIR, coderName, batchStub + '-evts.txt')

def vcode_filename(sessKey, coderName, short=False):
    '''Return full path to expected VCode file for a given study, session & coder. short=True to use just the session ID instead of exp + session.'''
    (expId, shortSess) = parse_session_key(sessKey)
    if short:
        return os.path.join(CODING_DIR, coderName, shortSess + '-evts.txt')
    else:
        return os.path.join(CODING_DIR, coderName, expId + '_' + shortSess + '-evts.txt')


def codesheet_filename(expId, coderName):
    '''Return full path to the .csv coding file for experiment expId & coderName'''
    return os.path.join(CODING_DIR, expId + '_' + coderName + '.csv')

def batchsheet_filename(expId, coderName):
    '''Return full path to the .csv batch file for experiment expId & coderName'''
    return os.path.join(CODING_DIR, expId + '_batches_' + coderName + '.csv')


def accountsheet_filename():
    '''Return full path to the .csv account file'''
    return os.path.join(CODING_DIR, 'accounts' + conf.VERSION + '.csv')


def make_session_key(expId, sessId):
    if conf.VERSION == 'prod':
        return 'lookit.session' + expId + 's.' + sessId
    else:
        return 'experimenter.session' + expId + 's.' + sessId

def parse_session_key(sessKey):
    if conf.VERSION == 'staging':
        prefix = 'experimenter.session'
    elif conf.VERSION == 'prod':
        prefix = 'lookit.session'
    assert sessKey[:len(prefix)] == prefix
    sessKey = sessKey[len(prefix):]
    (expId, sessId) = sessKey.split('.')
    assert expId[-1] == 's'
    expId = expId[:-1]
    return (expId, sessId)

def parse_expId(expId):
    '''parse an experiment id of the form *.ACTUALID'''
    pieces = expId.split('.')
    id = pieces[-1]
    # prefix = '.'.join(pieces[:-1])
    return id

def parse_videoname(vidName):
    '''Extracts meaningful pieces of video name.

    videos are named
    videoStream_video-record-<experiment.id>-<frame.id>-
       <session.id>_<timestamp>.flv, e.g.
          videoStream_video-consent-574db6fa3de08a005bb8f844-0-video-consent-574f62863de08a005bb8f8b8_1464820374637_240.flv
          videoStream_57586a553de08a005bb8fb7f_1-video-consent_PREVIEW_DATA_DISREGARD_1465935820244_351.flv

    '''

    assert vidName[-4:] == '.flv'
    fname = vidName[:-4]
    pieces = fname.split('_')

    assert len(pieces) >= 4

    expId = pieces[1]
    frameId = pieces[2]
    if vidName.find('PREVIEW_DATA_DISREGARD') > 0:
        sessId = 'PREVIEW_DATA_DISREGARD'
    else:
        sessId = pieces[3]
    timestamp = '_'.join(pieces[-2:])

    # shortname is what's recorded in the session data as the video expected.
    # It's missing the videoStream_ prefix and the timestamp_random.flv.
    # ex:
    # video-record-57472c903de08a0054472a02-2-video-1-574f693f3de08a005bb8f8e2
    shortnamePieces = fname.split('_')
    assert len(shortnamePieces) > 2
    shortname = '_'.join(shortnamePieces[1:-2])

    return (expId, frameId, sessId, timestamp, shortname)

def get_videolist():
    '''Return the list of .flv files in the video directory'''
    return [f for f in os.listdir(VIDEO_DIR) if \
                    not(os.path.isdir(os.path.join(VIDEO_DIR, f))) and \
                    f[-4:] in ['.flv'] ]

def get_batchfiles():
    '''Return the list of video files in the batch directory'''
    return [f for f in os.listdir(BATCH_DIR) if \
                    not(os.path.isdir(os.path.join(BATCH_DIR, f))) and \
                    f[-4:] in ['.flv', '.mp4'] ]
