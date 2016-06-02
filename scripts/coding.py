import os
import errno
import pickle
from client import EmailPreferences, Account, SendGrid, ExperimenterClient
from utils import make_sure_path_exists, indent, timestamp
import pprint
import uuid
import subprocess as sp
import sys
import videoutils

# To use:
#    Set up .env file
#    Install AWS command-line tools:
#       http://docs.aws.amazon.com/cli/latest/userguide/installing.html
#       sudo pip install awscli
#    aws configure
#       enter keys (saved; can make new keys from AWS console)
#       region: us-east-1
#    pip install numpy


# Local data storage overview
#
# .env file defines:
# 	Video directory (where raw videos live)
# 	Batch video directory (where batched videos live)
# 	Coding directory (where human-readable spreadsheets live)
# Coder names
# 	Data directory (everything below is data)
#
# Coding: dict with sessionid as keys, values are dicts with structure:
# 	Consent
# 	coderComments
# 	coderName
#   videosExpected: list of video filenames expected, based on session data
#
# Sessions: array of dicts each with the following structure (directly from server):
# 	Attributes
# 		Feedback
# 		Sequence
# 		expData
# 			[frame-name]
# 				eventTimings
# 					eventType (nextFrame, ...)
# 					timestamp
# 				formData
# 					[custom-field]
# 		experimentId
# 		profileId (username.child)
# 		conditions
# 		completed
# 		hasReadFeedback
# 	meta
# 		created-on
# 	id (sessionid)
#
# Batch: keys are unique batch IDs
# 	batchFile: filename of batch
# 	videos: ordered list of (sessionId, videoname) pairs
# 	codedBy: set of coder names
#
# Videos: keys are filenames
#   shortName - subset of video name as used by sessions
#   framerate
#   duration
#   expId
#   sessId
#   inBatches (key=batchId)
#      position
#
#
# TODO: eventually encapsulate as a class that handles one experiment, and
#   can load/manipulate data



OSF_ACCESS_TOKEN = os.environ.get('OSF_ACCESS_TOKEN')
SENDGRID_KEY = os.environ.get('SENDGRID_KEY')
CODERS = eval(os.environ['CODERS'])
for d in ["VIDEO_DIR", "BATCH_DIR", "DATA_DIR", "CODING_DIR"]:
    make_sure_path_exists(os.environ.get(d))
printer = pprint.PrettyPrinter(indent=4)


def backup_and_save(filepath, object):
    '''Pickle object and save it to filepath, backup any existing file first.

    Note that this will overwrite any other backup files that share a timestamp.'''

    # move existing file to backup/timestamp/filepath
    if os.path.exists(filepath):
        (fileDir, fileName) = os.path.split(filepath)
        newDir = os.path.join(fileDir, 'backup', timestamp())
        make_sure_path_exists(newDir)
        os.rename(filepath, os.path.join(newDir, fileName))

    # then save in intended location
    with open(filepath,'wb') as f:
        pickle.dump(object, f, protocol=2)

def session_filename(expId):
    '''Return full path to the session data filename for experiment expId'''
    return os.path.join(os.environ.get('DATA_DIR'), 'session_data_' + \
        expId + '.bin')

def coding_filename(expId):
    '''Return full path to the coding data filename for experiment expId'''
    return os.path.join(os.environ.get('DATA_DIR'), 'coding_data_' + \
        expId + '.bin')

def batch_filename(expId):
    '''Return full path to the batch data filename for experiment expId'''
    return os.path.join(os.environ.get('DATA_DIR'), 'batch_data_' + \
        expId + '.bin')

def video_filename():
    '''Return full path to the video data filename (all experiments)'''
    return os.path.join(os.environ.get('DATA_DIR'), 'video_data.bin')

def get_videolist():
    '''Return the list of .flv files in the video directory'''
    videoDir = os.environ.get('VIDEO_DIR')
    return [f for f in os.listdir(videoDir) if \
                    not(os.path.isdir(os.path.join(videoDir, f))) and \
                    f[-4:] in ['.flv'] ]

def get_batchfiles():
    '''Return the list of video files in the batch directory'''
    videoDir = os.environ.get('BATCH_DIR')
    return [f for f in os.listdir(videoDir) if \
                    not(os.path.isdir(os.path.join(videoDir, f))) and \
                    f[-4:] in ['.flv', '.mp4'] ]

def update_session_data(experimentId, display=False):
    '''Get session data from the server for each experiment ID and save'''
    client = ExperimenterClient(access_token=OSF_ACCESS_TOKEN).authenticate()
    exps = client.fetch_experiments()
    expIDs = [parse_expId(exp['id']) for exp in exps]

    iExp = expIDs.index(experimentId)
    exp = exps[iExp]
    exp['sessions'] = client.fetch_sessions_for_experiment(exp)

    backup_and_save(session_filename(experimentId), exp)

    if display:
        printer.pprint(exp['sessions'])

    print "Updated session data for experiment: " + experimentId

def load_session_data(expId):
    '''Return saved session data for this experiment. Error if no saved data.'''
    with open(session_filename(expId),'rb') as f:
        exp = pickle.load(f)
    return exp

def load_batch_data(expId):
    '''Return saved batch data for this experiment. Empty if no data.'''
    batchFile = batch_filename(expId)
    if os.path.exists(batchFile):
        with open(batch_filename(expId),'rb') as f:
            batches = pickle.load(f)
        return batches
    else:
        return {}

def load_coding(expId):
    '''Return saved coding data for this experiment, or empty dict if none saved.'''
    codingFile = coding_filename(expId)
    if os.path.exists(codingFile):
        with open(codingFile,'rb') as f:
            coding = pickle.load(f)
    else:
        coding = {}
    return coding

def load_video_data():
    '''Return saved coding data for this experiment, or empty dict if none saved.'''
    videoFile = video_filename()
    if os.path.exists(videoFile):
        with open(videoFile,'rb') as f:
            videoData = pickle.load(f)
    else:
        videoData = {}
    return videoData

def update_video_data(newVideos=[], replace=False, whichStudies=[]):

    videoData = load_video_data()
    videoFilenames = get_videolist()

    if len(newVideos) == 0:
        newVideos = list(set(videoFilenames) - set(videoData.keys()))

    allCoding = {}

    sessionsAffected = []

    for vidName in newVideos:
        try:
            (expId, frameId, sessId, timestamp) = parse_videoname(vidName)
        except AssertionError:
            print "Unexpected videoname format: " + vidName
            # TODO: add these to a list at the end.
            continue
        key = 'experimenter.session' + expId + 's.' + sessId

        if len(whichStudies) > 0 and expId not in whichStudies:
            continue

        if expId not in allCoding.keys():
            allCoding[expId] = load_coding(expId)
        coding = allCoding[expId]

        if key not in coding.keys():
            print """ Could not find session!
                vidName: {}
                sessId from filename: {}
                key from filename: {}
                actual keys: {}
                """.format(
                  vidName,
                  sessId,
                  key,
                  allCoding[expId].keys()
                )
            continue

        if vidName not in videoData.keys() or replace:
            sessionsAffected.append(key)
            (nFrames, dur, dims) = videoutils.get_framerate(vidName, 0.1)
            videoData = {'framerate': nFrames/dur,
                     'duration': dur,
                     'sessId': sessId,
                     'expId': expId,
                     'inBatches': {} }

            videoData[vidName] = videoData

    backup_and_save(video_filename(), videoData)
    return sessionsAffected



def add_batch(expId, batchFilename, videos):
    '''Add a batched video.

    expId: experiment id, string
        (ex.: 574db6fa3de08a005bb8f844)
    batchFilename: filename of batch video file (not full path)
    videos: ordered list of (sessionId, videoFilename) pairs.
        sessionId is an index into the coding directory, videoFilename
        is the individual filename (not full path).

    The batch data file for this experiment will be updated as well
    as the coding data.'''

    # Load existing batch data
    batches = load_batch_data(expId)

    # Create a batch dict for this batch
    bat = { 'batchFile': batchFilename,
            'videos': videos,
            'codedBy': [] }

    # Add this batch to the existing batches and save
    batId = uuid.uuid4().hex
    batches[batId] = bat

    backup_and_save(batch_filename(expId), batches)

    # Add references to this batch in each coding record affected
    coding = load_coding(expId)
    for (iVid, (sessionId, videoname)) in videos:
        coding[sessionId]['videos'][videoname]['inBatches'][batId] = iVid
    backup_and_save(coding_filename(expId), coding)

def remove_batch(expId, batchId):
    '''Remove a batched video from the data files (batch and coding data)'''

    # Load existing batch data
    batches = load_batch_data(expId)

    # Remove this batch
    del batches[batchId]

    backup_and_save(batch_filename(expId), batches)

    # Remove references to this batch in each coding record affected
    coding = load_coding(expId)
    for (iVid, (sessionId, videoname)) in videos:
        del coding[sessionId]['videos'][videoname]['inBatches'][batchId]
    backup_and_save(coding_filename(expId), coding)

def empty_coding_record():
    '''Return a new instance of an empty coding dict'''
    return {'consent': 'orig',
            'coderComments': {}, # CoderName: 'comment'
            'videos': {}, # Videoname: framerate, length, {batch#: position}
            'videosExpected': []}

def update_coding(expId, display=False):
    '''Update coding data with empty records for any new sessions in saved session data.'''

    exp = load_session_data(expId)
    updated = False

    # Load coding file. If it doesn't exist, start with an empty dict.
    coding = load_coding(expId)

    # If any existing coding records are missing expected fields, add them
    for (sessId, code) in coding.iteritems():
        empty = empty_coding_record()
        for missingKey in set(empty.keys()) - set(code.keys()):
            code[missingKey] = empty[missingKey]
            updated = True

    sessIds = [exp['sessions'][iSess]['id'] for iSess in \
                    range(len(exp['sessions']))]
    newIds = list(set(sessIds) - set(coding.keys()))
    newCoding = dict((k, empty_coding_record()) for k in newIds)

    coding.update(newCoding)

    for iSess in range(len(exp['sessions'])):
        sessId = exp['sessions'][iSess]['id']
        expData = exp['sessions'][iSess]['attributes']['expData']
        coding[sessId]['videosExpected'] = []
        for (frameId, frameData) in expData.iteritems():
            if 'videoId' in frameData.keys():
                coding[sessId]['videosExpected'].append(frameData['videoId'])

    backup_and_save(coding_filename(expId), coding)

    if display:
        printer.pprint(coding)

    print "Updated coding for experiment: " + expId

def show_all_experiments():
    '''Display a list of all experiments listed on the server (no return value)'''
    client = ExperimenterClient(access_token=OSF_ACCESS_TOKEN).authenticate()
    exps = client.fetch_experiments()
    for (iExp, exp) in enumerate(exps):
        print  exp['id'] + ' ' + exp['attributes']['title']

def parse_expId(expId):
    '''parse an experiment id of the form *.ACTUALID'''
    pieces = expId.split('.')
    id = pieces[-1]
    prefix = '.'.join(pieces[:-1])
    return id

def parse_videoname(vidName):
    '''Extracts meaningful pieces of video name.

    videos are named
    videoStream_video-record-<experiment.id>-<frame.id>-
       <session.id>_<timestamp>.flv, e.g.
          videoStream_video-consent-574db6fa3de08a005bb8f844-0-video-consent-574f62863de08a005bb8f8b8_1464820374637_240.flv

    '''


    assert vidName[-4:] == '.flv'
    fname = vidName[:-4]
    pieces = fname.split('-')

    assert len(pieces) >= 4

    expId = pieces[2]
    frameId = '-'.join(pieces[3:-1])
    last = pieces[-1]
    lastPieces = last.split('_')
    sessId = lastPieces[0]
    timestamp = '_'.join(lastPieces[1:])

    return (expId, frameId, sessId, timestamp)

def sync_S3():
    '''Download any new or modified video files from S3.'''
    origVideos = get_videolist()
    sp.check_call(['aws', 's3', 'sync', 's3://mitLookit', os.environ.get('VIDEO_DIR'), '--only-show-errors'])
    allVideos = get_videolist()
    newVideos = list(set(allVideos)-set(origVideos))
    print "Downloaded videos:"
    print(indent(printer.pformat(newVideos), 4))
    return newVideos

def store_framerates(vidList, whichExp):
    '''Go through the list of videos and update framerates (in coding data) for any that are part of whichExp. Warn about any that are part of this experiment but don't have a corresponding session.'''

    coding = load_coding(whichExp)

    sessionsAffected = []

    for vidName in newVideos:
        try:
            assert False
            (expId, frameId, sessId, timestamp) = parse_videoname(vidName)
        except AssertionError:

            print "Unexpected videoname format: " + vidName
            continue
        key = 'experimenter.session' + expId + 's.' + sessId

        if expId != whichExp:
            continue

        (nFrames, dur, dims) = videoutils.get_framerate(vidName, 0.1)

        if key in coding.keys():
            print "Found session for this video!"
            sessionsAffected.append(key)
            videoData = {'framerate': nFrames/dur,
                         'duration': dur,
                         'inBatches': {}} # TODO HERE: add shortname
            if vidName in coding[key]['videos'].keys():
                     allCoding[expId][key]['videos'][vidName]['framerate'] = nFrames/dur
                     allCoding[expId][key]['videos'][vidName]['duration'] = dur
            else:
                coding[key]['videos'][vidName] = videoData

        else:
            print """ Did not find session!
                vidName: {}
                sessId from filename: {}
                key from filename: {}
                actual keys: {}
                """.format(
                  vidName,
                  sessId,
                  key,
                  allCoding[expId].keys()
                )

    backup_and_save(coding_filename(whichExp), coding)
    return sessionsAffected


if __name__ == '__main__':

    physID = '574db6fa3de08a005bb8f844'
    testID = '57472c903de08a0054472a02'

    cmds = sys.argv[1:]
    if 'doUpdate' in cmds:
        for id in [physID, testID]:
            update_session_data(id, display=True)
            update_coding(id, display=True)
        newVideos = sync_S3()
        #sessionsAffected = store_framerates(newVideos, testID)
        sessionsAffected = update_video_data(replace=False, whichStudies=[physID, testID])
        print sessionsAffected

    elif 'test' in cmds:
        show_all_experiments()
        fname = 'videoStream_video-consent-574db6fa3de08a005bb8f844-0-video-consent-574f62863de08a005bb8f8b8_1464820374637_240.flv'
        parse_videoname(fname)

        #just missing videoStream_ and timestamp.flv at end.
        #video-record-57472c903de08a0054472a02-2-video-1-574f693f3de08a005bb8f8e2

    else:
        client = ExperimenterClient(access_token=OSF_ACCESS_TOKEN).authenticate()
        exps = client.fetch_experiments()
        expIDs = [exp['id'] for exp in exps]
        expTitles = [exp['attributes']['title'] for exp in exps]

        physID = 'experimenter.experiments.574db6fa3de08a005bb8f844'

        iPhys = expIDs.index(physID)
        exp = exps[iPhys]
        exp['sessions'] = client.fetch_sessions_for_experiment(exp)

        accounts = client.fetch_accounts()
        for acc in accounts:
            printer.pprint(acc.id)
            printer.pprint(acc.name)
            printer.pprint(acc.email)

        print """
        Experiment title: {}
        \tSessions: {}
        """.format(
           exp['attributes']['title'],
           len(exp['sessions'])
        )

        for iSess in range(len(exp['sessions'])):
            sess = exp['sessions'][iSess]
            attr = sess['attributes']

            print "Session: {}".format(iSess)

            if '4-4-exit-survey' in attr['expData'].keys():
                print "\tExit comments: " +  attr['expData']['4-4-exit-survey']['formData']['feedback']

            print """
            Parent.child: {}
            Date: {}
            Feedback: {}
            Conditions: {}
            Completed: {}
            hasReadFeedback: {}
            expData.keys(): {}
            """.format(
                    attr['profileId'],
                    sess['meta']['created-on'],
                    attr['feedback'],
                    attr.get('conditions', []),
                    attr['completed'],
                    attr['hasReadFeedback'],
                    attr['expData'].keys(),
                    attr.keys()   )

            print """\tMood data:"""
            print(indent(printer.pformat(attr['expData'].get('3-3-mood-survey', [])), 8))

            printer.pprint(attr['expData'])

            #res = client.set_session_feedback(sess, "Here's some exciting test feedback! Your baby is so cute! Child:" + attr['profileId'])
