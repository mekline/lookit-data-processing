import os
import errno
import pickle
from client import Account, SendGrid, ExperimenterClient
from utils import make_sure_path_exists, indent, timestamp, printer, backup_and_save, flatten_dict, backup, backup_and_save_dict
import uuid
import subprocess as sp
import sys
import videoutils
from warnings import warn
import datetime
import lookitpaths as paths
from updatefromlookit import sync_S3, pull_from_wowza, update_account_data, show_all_experiments, update_session_data
import csv
import random
import string

# TODO: eventually encapsulate as a class that handles one experiment, and
#   can load/manipulate data



def find_session(sessionData, sessionKey):
    for sess in sessionData['sessions']:
        if sess['id'] == sessionKey:
            return sess
    return -1

def load_batch_data(expId):
    '''Return saved batch data for this experiment. Empty if no data.'''
    batchFile = paths.batch_filename(expId)
    if os.path.exists(batchFile):
        with open(batchFile,'rb') as f:
            batches = pickle.load(f)
        return batches
    else:
        return {}

def load_session_data(expId):
    '''Return saved session data for this experiment. Error if no saved data.'''
    with open(paths.session_filename(expId),'rb') as f:
        exp = pickle.load(f)
    return exp

def load_coding(expId):
    '''Return saved coding data for this experiment, or empty dict if none saved.'''
    codingFile = paths.coding_filename(expId)
    if os.path.exists(codingFile):
        with open(codingFile,'rb') as f:
            coding = pickle.load(f)
    else:
        coding = {}
    return coding

def load_video_data():
    '''Return video data, or empty dict if none saved.'''
    if os.path.exists(paths.VIDEO_FILENAME):
        with open(paths.VIDEO_FILENAME,'rb') as f:
            videoData = pickle.load(f)
    else:
        videoData = {}
    return videoData

def load_account_data():
    '''Return saved account data, or empty dict if none saved.'''
    if os.path.exists(paths.ACCOUNT_FILENAME):
        with open(paths.ACCOUNT_FILENAME,'rb') as f:
            accountData = pickle.load(f)
    else:
        accountData = {}
    return accountData



def update_video_data(newVideos=[], reprocess=False, resetPaths=False, whichStudies=[], display=False):
    '''Updates video data file.

    keyword args:
    newVideos: If [] (default), process all video names in the video directory
        that are not already in the video data file. Otherwise process only the
        list newVideos. Should be a list of filenames to find in VIDEO_DIR. If
        'all', process all video names in the video directory.
    reprocess: Whether to reprocess filenames that are already in the data file.
        If true, recompute framerate/duration (BUT DO NOT CLEAR BATCH DATA).
        Default false (skip filenames already there). Irrelevant if
        newVideos==[].
    resetPaths: Whether to reset mp4Path/mp4Dur fields (e.g. mp4Path_whole,
        mp4Path_trimmed) to ''/-1 (default False)
    whichStudies: list of study IDs for which to update data. Skip filenames for
        other studies, do not add to video data. If [] process all studies.

    Returns:
    (sessionsAffected, improperFilenames, unmatchedVideos)

    sessionsAffected: list of sessionIds (as for indexing into coding)
    improperFilenames: list of filenames skipped because they couldn't be parsed
    unmatchedFilenames: list of filenames skipped because they couldn't be
        matched to any session data

    '''

    # Get video data and current list of videos
    videoData = load_video_data()
    videoFilenames = paths.get_videolist()

    # Parse newVideos input
    if len(newVideos) == 0:
        newVideos = list(set(videoFilenames) - set(videoData.keys()))
    elif newVideos=="all":
        newVideos = videoFilenames

    print "Updating video data. Processing {} videos.".format(len(newVideos))

    allSessData = {}

    sessionsAffected = []
    improperFilenames = []
    unmatchedFilenames = []

    for vidName in newVideos:
        # Parse the video name and check format
        try:
            (expId, frameId, sessId, timestamp, shortname) = paths.parse_videoname(vidName)
        except AssertionError:
            print "Unexpected videoname format: " + vidName
            improperFilenames.append(vidName)
            continue
        key = paths.make_session_key(expId, sessId)

        # Skip videos for other studies
        if len(whichStudies) > 0 and expId not in whichStudies:
            continue

        # Get session data if needed
        if expId not in allSessData.keys():
            allSessData[expId] = load_session_data(expId)

        sessionData = allSessData[expId]['sessions']

        # Don't enter videos from the experimenter site, since we don't have
        # corresponding session/coding info
        if sessId == 'PREVIEW_DATA_DISREGARD':
            if display:
                print "Preview video - skipping"
            continue;

        # Check that we can match this to a session
        if key not in [s['id'] for s in sessionData]:
            print """ Could not find session!
                vidName: {}
                sessId from filename: {}
                key from filename: {}
                actual keys (examples): {}
                """.format(
                  vidName,
                  sessId,
                  key,
                  [s['id'] for s in sessionData[:10]]
                )
            unmatchedFilenames.append(vidName)
            continue

        # Update info if needed (i.e. if replacing or don't have this one yet)
        alreadyHaveRecord = (vidName in videoData.keys())
        if (not alreadyHaveRecord) or (reprocess or resetPaths):

            sessionsAffected.append(key) # Keep track of this session

            # Start from either existing record or any default values that need to be added
            if alreadyHaveRecord:
                thisVideo = videoData[vidName]
            else:
                thisVideo = {'inBatches': {}}

            # Add basic attributes
            thisVideo['shortname'] = shortname
            print shortname # TODO: remove
            thisVideo['sessionKey'] = key
            thisVideo['expId'] = expId

            # Add framerate/etc. info if needed
            if reprocess or not alreadyHaveRecord:
                (nFrames, dur, bitRate) = videoutils.get_video_details(vidName, ['nframes', 'duration', 'bitrate'])
                thisVideo['framerate'] = nFrames/dur
                thisVideo['duration'] = dur
                thisVideo['bitRate'] = bitRate

            # Add default path values if needed
            if resetPaths or not alreadyHaveRecord:
                thisVideo['mp4Dur_whole'] = -1
                thisVideo['mp4Path_whole'] = ''
                thisVideo['mp4Dur_trimmed'] = -1
                thisVideo['mp4Path_trimmed'] = ''

            if display:
                print "Processed {}: framerate {}, duration {}".format(vidName,
                    thisVideo['framerate'], thisVideo['duration'])

            videoData[vidName] = thisVideo

    # Save the video data file
    backup_and_save(paths.VIDEO_FILENAME, videoData)

    return (sessionsAffected, improperFilenames, unmatchedFilenames)

def update_videos_found(expId):
    '''Use coding & video data to match expected videoname fragments to received videos.

    expId: experiment id, string
        (ex.: 574db6fa3de08a005bb8f844)

    Uses partial filenames in coding[sessKey]['videosExpected'] and searches for
    videos in the videoData that match the expected pattern. The field
    coding[sessKey]['videosFound'] is created or updated to correspond to
    coding[sessKey]['videosExpected']. ...['videosFound'][i] is a list of
    video filenames within VIDEO_DIR that match the pattern in
    ...['videosExpected'][i].

    Currently this is very inefficient--rechecks all sessions in the experiment.
    Note that this does not update the coding or video data; these should
    already be up to date.'''

    print "Updating videos found for study {}", expId

    # Retrieve coding and video data
    coding = load_coding(expId)
    videoData = load_video_data()

    # Process each session...
    for sessKey in coding.keys():
        # Process the sessKey and check this is the right experiment
        (expIdKey, sessId) = paths.parse_session_key(sessKey)

        # Which videos do we expect? Skip if none.
        shortNames = coding[sessKey]['videosExpected']
        if len(shortNames) == 0:
            continue;

        # Which videos match the expected patterns? Keep track & save the list.
        coding[sessKey]['videosFound'] = []
        for (iShort, short) in enumerate(shortNames):
            theseVideos = [k for (k,v) in videoData.items() if (v['shortname']==short) ]
            if len(theseVideos) == 0:
                warn('update_videos_found: Expected video not found for {}'.format(short))
            coding[sessKey]['videosFound'].append(theseVideos)

    # Save coding & video data
    backup_and_save(paths.coding_filename(expId), coding)


def make_mp4s(sessDirRel, vidNames, display=False, trimming=False, suffix='', replace=False):
    '''Convert flvs in VIDEO_DIR to mp4s organized in SESSION_DIR for a particular session

    sessDirRel: relative path to session directory where mp4s should be saved.
        mp4s will be created in paths.SESSION_DIR/sessDirRel.

    vidNames: list of video names (flv filenames within VIDEO_DIR, also keys
        into videoData) to convert

    display: whether to display information about progress

    trimming: False (default) not to do any trimming of video file, or a maximum
        clip duration in seconds. The last trimming seconds (counted from the
        end of the shortest stream--generally video rather than audio) will be
        kept, or if the video is shorter than trimming, the entire video will be
        kept.

    suffix: string to append to the mp4 filenames (they'll be named as their
        originating flv filenames, plus "_[suffix]") and to the fields
        'mp4Path_[suffix]' and 'mp4Dur_[suffix]' in videoData. Default ''.

    replace: False (default) to skip making an mp4 if (a) we already have the
        correct filename and (b) we have a record of it in videoData, True to
        make anyway.

    To make the mp4, we first create video-only and audio-only files from
    the original flv file. Then we put them together and delete the temporary
    files. The final mp4 has a duration equal to the length of the video stream
    (technically it has a duration equal to the shorter of the audio and video
    streams, but generally video is shorter, and we pad the audio stream with
    silence in case it's shorter). Trimming, however, is done (to the best of
    my understanding) from the end of the longest stream. This is appropriate
    since it is possible for audio to continue to the end of a
    recording period, while video gets cut off earlier due to the greater
    bandwidth required.

    mp4s have a text label in the top left that shows
    [segment]_[session]_[timestamp and randomstring] from the original flv name.

    Returns a dictionary with keys = vidNames. Each value is a dict with the
    following fields:
    'mp4Dur_[suffix]': 0 if no video was able to be created, due to missing
        video or a missing video stream. It is also possible for video not
        to be created if there is a video stream, but it stops and then the
        audio stream continues for at least trimming seconds after that.
    'mp4Path_[suffix]': Relative path (from paths.SESSION_DIR) to mp4 created,
        or '' if as above mp4 was not created.

    (Does NOT save anything directly to videoData, since this may be called
    many times in short succession!)'''

    # Convert each flv clip to mp4 & get durations
    allVideoData = load_video_data()
    vidData = {}
    concat = [paths.FFMPEG]
    loglevel = 'quiet'

    # Get full path to the session directory
    sessionDir = os.path.join(paths.SESSION_DIR, sessDirRel)

    # Keep track of whether we
    madeAnyFiles = False

    for (iVid, vid) in enumerate(vidNames):
        vidPath = os.path.join(paths.VIDEO_DIR, vid)

        # If not replacing: check that we haven't already (tried to) make this mp4
        mergedFilename = vid[:-4] + '_' + suffix + '.mp4'
        mergedPath = os.path.join(sessionDir, mergedFilename)
        if not replace and os.path.exists(mergedPath) and vid in allVideoData.keys() and ('mp4Dur_' + suffix) in allVideoData[vid].keys() and ('mp4Path_' + suffix) in allVideoData[vid].keys():
            if display:
                print "Already have {} mp4 for video {}, skipping".format(suffix, vid)
            continue

        # Add this to the video data file, with default values in case we can't
        # actually create the mp4 file (video data missing).
        vidData[vid] = {}
        vidData[vid]['mp4Dur' + '_' + suffix] = 0
        vidData[vid]['mp4Path' + '_' + suffix] = ''

        # Check that we actually have any video data in the original
        height, origDur = videoutils.get_video_details(vid, ['height', 'duration'])
        if height == 0:
            warn('No video data for file {}'.format(vid))
            continue

        trimStrVideo = ''
        trimStrAudio = ''
        if trimming:
            startTimeVideo = max(0, origDur - trimming)
            startTimeAudio = max(0, origDur - trimming)
            trimStrVideo = ",trim=" + str(startTimeVideo)+":,setpts=PTS-STARTPTS"
            trimStrAudio = "asetpts=PTS-STARTPTS,atrim="+ str(startTimeAudio)+':,'

        # Make video-only file
        (_, frameId, sessStr, timestamp, _) = paths.parse_videoname(vid)
        filterComplexVideo = "[0:v]drawtext='fontfile=/Library/Fonts/Arial Black.ttf':text='"+frameId + '_' + '_' + sessStr + '_' + timestamp + "':fontsize=12:fontcolor=red:x=10:y=10,setpts=PTS-STARTPTS" + trimStrVideo + "[v0]"
        noAudioPath = os.path.join(sessionDir, vid[:-4] + '_video.mp4')
        sp.call([paths.FFMPEG, '-i', vidPath, '-filter_complex',
filterComplexVideo, '-map', '[v0]', '-c:v', 'libx264', '-an', '-vsync', 'cfr', '-r', '30', '-crf', '18', noAudioPath, '-loglevel', loglevel])
        madeAnyFiles = True

        # Check that the last N seconds contain video
        videoOnlyDur = videoutils.get_video_details(noAudioPath, ['duration'], fullpath=True)

        if videoOnlyDur > 0:
            if display:
                print "Making {} mp4 for vid: {}".format(suffix, vid)

            # Make audio-only file
            filterComplexAudio = '[0:a]' + trimStrAudio + 'asetpts=PTS-STARTPTS,apad=pad_len=100000'
            audioPath = os.path.join(sessionDir, vid[:-4] + '_audio.m4a')
            sp.call([paths.FFMPEG, '-i', vidPath, '-vn', '-filter_complex', filterComplexAudio, '-c:a', 'libfdk_aac', '-loglevel', loglevel, audioPath])

            # Put audio and video together
            sp.call([paths.FFMPEG, '-i', noAudioPath,  '-i', audioPath, '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-loglevel', loglevel, mergedPath])

            # Check the duration of the newly created clip
            (dur, startTime) = videoutils.get_video_details(mergedPath, ['duration', 'starttime'],  fullpath=True)

            # Save the (relative) path to the mp4 and its duration
            vidData[vid] = {}
            vidData[vid]['mp4Dur' + '_' + suffix] = dur
            vidData[vid]['mp4Path' + '_' + suffix] = os.path.join(sessDirRel, mergedFilename)


    # Clean up intermediate audio/video-only files
    if madeAnyFiles:
        sp.call('rm ' + os.path.join(sessionDir, '*_video.mp4'), shell=True)
        sp.call('rm ' + os.path.join(sessionDir, '*_audio.m4a'), shell=True)

    return vidData

def concat_mp4s(concatPath, vidPaths):
    '''Concatenate a list of mp4s into a single new mp4.

    concatPath: full path to the desired new mp4 file, including extension
    vidPaths: relative paths (within paths.SESSION_DIR) to the videos to
        concatenate. Videos will be concatenated in the order they appear
        in this list.

    Return value: vidDur, the duration of the video stream of the concatenated
        mp4 in seconds. vidDur is 0 if vidPaths is empty, and no mp4 is created.
        '''

    concat = [paths.FFMPEG]
    loglevel = 'quiet'
    inputList = ''

    # If there are no files to concat, immediately return 0.
    if not len(vidPaths):
        return 0

    # Build the concatenate command
    for (iVid, vid) in enumerate(vidPaths):
        concat = concat + ['-i', os.path.join(paths.SESSION_DIR, vid)]
        inputList = inputList + '[{}:0][{}:1]'.format(iVid, iVid)

    # Concatenate the videos
    concat = concat + ['-filter_complex', inputList + 'concat=n={}:v=1:a=1'.format(len(vidPaths)) + '[out]', '-map', '[out]', concatPath, '-loglevel', 'error']
    sp.call(concat)

    # Check and return the duration of the video stream
    vidDur = videoutils.get_video_details(concatPath, 'vidduration', fullpath=True)
    return vidDur

def make_mp4s_for_study(expId, sessionsToProcess='missing', display=False, trimming=False, suffix=''):
    '''Convert flvs to mp4s for sessions in a particular study.

    expId: experiment id, string
        (ex.: 574db6fa3de08a005bb8f844)

    sessionsToProcess: 'missing', 'all', or a list of session keys (as used to
        index into coding). 'missing' creates mp4s only if they don't already
        exist (both video file and entry in videoData). 'all' creates mp4s for
        all session flvs, even if they already exist.

    display: (default False) whether to print out information about progress

    trimming: False (default) not to do any trimming of video file, or a maximum
        clip duration in seconds. The last trimming seconds (counted from the
        end of the shortest stream--generally video rather than audio) will be
        kept, or if the video is shorter than trimming, the entire video will be
        kept. As used by make_mp4s.

    suffix: string to append to the mp4 filenames (they'll be named as their
        originating flv filenames, plus "_[suffix]") and to the fields
        'mp4Path_[suffix]' and 'mp4Dur_[suffix]' in videoData. Default ''.
        As used by make_mp4s.

    Calls make_mp4s to actually create the mp4s; see documentation there.

    The following values are set in videoData[video]:
    'mp4Dur_[suffix]': 0 if no video was able to be created, due to missing
        video or a missing video stream. It is also possible for video not
        to be created if there is a video stream, but it stops and then the
        audio stream continues for at least trimming seconds after that.
    'mp4Path_[suffix]': Relative path (from paths.SESSION_DIR) to mp4 created,
        or '' if as above mp4 was not created.'''

    print "Making {} mp4s for study {}".format(suffix, expId)

    # Retrieve coding and video data
    coding = load_coding(expId)
    videoData = load_video_data()

    if sessionsToProcess in ['missing', 'all']:
        sessionKeys = coding.keys()
    else:
        # Make sure list of sessions is unique
        sessionKeys = list(set(sessionsToProcess))

    # Don't have ffmpeg tell us everything it has ever thought about.
    loglevel = 'quiet'

    # Process each session...
    for sessKey in sessionKeys:
        # Process the sessKey and check this is the right experiment
        (expIdKey, sessId) = paths.parse_session_key(sessKey)
        if not expIdKey == expId:
            print "Skipping session not for this ID: {}".format(sessKey)
            continue

        # Which videos do we expect? Skip if none.
        shortNames = coding[sessKey]['videosExpected']
        if len(shortNames) == 0:
            continue;

        # Expand the list of videos we'll need to process
        vidNames = []
        for vids in coding[sessKey]['videosFound']:
            vidNames = vidNames + vids

        # Choose a location for the concatenated videos
        sessDirRel = os.path.join(expId, sessId)
        sessionDir = os.path.join(paths.SESSION_DIR, sessDirRel)
        make_sure_path_exists(sessionDir)

        # Convert each flv clip to mp4 & get durations

        if display:
            print 'Session: ', sessId

        replace = sessionsToProcess == 'all'

        mp4Data = make_mp4s(sessDirRel, vidNames, display, trimming=trimming, suffix=suffix, replace=replace)

        for vid in mp4Data.keys():
            # Save the (relative) path to the mp4 and its duration in video data
            # so we can use it when concatenating these same videos into another
            # file
            videoData[vid]['mp4Path' + '_' + suffix] = mp4Data[vid]['mp4Path' + '_' + suffix]
            videoData[vid]['mp4Dur' + '_' + suffix] = mp4Data[vid]['mp4Dur' + '_' + suffix]


    # Save coding & video data
    backup_and_save(paths.VIDEO_FILENAME, videoData)

def concatenate_session_videos(expId, sessionKeys, replace=False, display=False):
    '''Concatenate videos within the same session for the specified sessions.

    Should be run after update_videos_found as it relies on videosFound in
    coding. Does create any missing _whole mp4s but does not replace existing
    ones.

    expId: experiment ID to concatenate videos for. Any sessions associated
        with other experiments will be ignored (warning shown).
    sessionKeys: 'all', 'missing', or a list of session keys to process,
        e.g. as returned by
        update_video_data. Session keys are the IDs in session data and the
        keys for the coding data.
    replace: whether to replace existing concatenated files (default False)
    display: whether to show debugging output (default False)

    For each session, this:
    - uses videosFound in the coding file to locate (after creating if
    necessary) single-clip mp4s (untrimmed) with text labels
    - creates a concatenated mp4 with all video for this session (in order)
    in SESSION_DIR/expId/sessId/, called expId_sessId.mp4

    Does not save any coding or video data.
    '''

    print "Making concatenated session videos for study {}".format(expId)

    # Retrieve coding and video data
    coding = load_coding(expId)
    videoData = load_video_data()

    if sessionKeys in ['missing', 'all']:
        sessionKeys = coding.keys()
    else:
        # Make sure list of sessions is unique
        sessionKeys = list(set(sessionKeys))

    # Don't have ffmpeg tell us everything it has ever thought about.
    loglevel = 'quiet'

    make_mp4s_for_study(expId, sessionsToProcess=sessionKeys, display=display, trimming=False, suffix='whole')

    # Process each session...
    for sessKey in sessionKeys:

        # Process the sessKey and check this is the right experiment
        (expIdKey, sessId) = paths.parse_session_key(sessKey)
        if not expIdKey == expId:
            print "Skipping session not for this ID: {}".format(sessKey)
            continue

        if display:
            print 'Session: ', sessKey

        # Choose a location for the concatenated videos
        sessDirRel = os.path.join(expId, sessId)
        sessionDir = os.path.join(paths.SESSION_DIR, sessDirRel)
        make_sure_path_exists(sessionDir)
        concatFilename = expId + '_' +  sessId + '.mp4'
        concatPath = os.path.join(sessionDir, concatFilename)

        # Skip if not replacing & file exists
        if not replace and os.path.exists(concatPath):
            print "Skipping, already have concat file: {}".format(concatFilename)
            continue

        # Which videos match the expected patterns? Keep track & save the list.
        vidNames = []
        for vids in coding[sessKey]['videosFound']:
            vidNames = vidNames + vids

        # Sort the vidNames found by timestamp so we concat in order.
        withTs = [(paths.parse_videoname(v)[3], v) for v in vidNames]
        vidNames = [tup[1] for tup in sorted(withTs)]
        vidNames = [v for vid in vidNames if len(videoData[vid]['mp4Path_whole'])] # TODO: this assumes we have mp4Path_whole in all cases

        if len(vidNames) == 0:
            warn('No video data for session {}'.format(sessKey))
            continue

        totalDur = 0
        for (iVid, vid) in enumerate(vidNames):
            totalDur = totalDur + videoData[vid]['mp4Dur_whole']

        # Concatenate mp4 videos

        vidDur = concat_mp4s(concatPath, [os.path.join(paths.SESSION_DIR, videoData[vid]['mp4Path_whole']) for vid in vidNames])

        if display:
            print 'Total duration: expected {}, actual {}'.format(totalDur, vidDur)
            # Note: "actual total dur" is video duration only, not audio or standard "overall" duration. This is fine for our purposes so far where we don't need exactly synchronized audio and video in the concatenated files (i.e. it's possible that audio from one file might appear to occur during a different file (up to about 10ms per concatenated file), but would need to be fixed for other purposes!

        # Warn if we're too far off (more than one video frame at 30fps) on
        # the total duration
        if abs(totalDur - vidDur) > 1./30:
            warn('Predicted {}, actual {}'.format(totalDur, vidDur))

def batch_videos(expId, batchLengthMinutes=5, codingCriteria={'consent':['yes'], 'usable':['yes']}, includeIncompleteBatches=True):
    ''' Create video batches for a study.

    expId: experiment id, string
        (ex.: 574db6fa3de08a005bb8f844)

    batchLengthMinutes: minimum batch length in minutes. Videos will be added
        to one batch until they exceed this length.

    codingCriteria: a dictionary of requirements on associated coding data
        for videos to be included in a batch. keys are keys within a coding
        record (e.g. 'consent') and values are lists of acceptable values.
        Default {'consent':['yes'], 'usable':['yes']}. Values are insensitive to
        case and leading/trailing whitespace.

    includeIncompleteBatches: whether to create a batch for the "leftover" files
        even though they haven't gotten to batchLengthMinutes long yet.

    Trimmed mp4s (ending in _trimmed.mp4) are used for the batches. These must
    already exist--call make_mp4s_for_study first. Only videos not currently in
    any batch will be added to a batch.

    Batch mp4s are named [expId]_[short random code].mp4 and are stored in
    paths.BATCH_DIR. Information about the newly created batches is stored in
    two places:
        - batch data: adds new mapping batchKey :
            {'batchFile': batchFilename,
             'videos': [(sessionKey, flvName, duration), ...] }
        - videoData: add videoData[flvName]['inBatches'][batchId] = index in
            batch

    '''

    print "Making video batches for study {}".format(expId)

    # Retrieve coding and video data
    coding = load_coding(expId)
    videoData = load_video_data()

    vidsToProcess = []

    # First, find all trimmed, not-currently-in-batches videos for this study.
    for sessKey in coding.keys():
        for vidList in coding[sessKey]['videosFound']:
            for vid in vidList:
                if 'mp4Path_trimmed' in videoData[vid].keys():
                    mp4Path = videoData[vid]['mp4Path_trimmed']
                    mp4Dur  = videoData[vid]['mp4Dur_trimmed']
                    if len(mp4Path) and mp4Dur and not len(videoData[vid]['inBatches']):
                        vidsToProcess.append((sessKey, vid))

    # Check for coding criteria (e.g. consent, usable)
    for (criterion, values) in codingCriteria.items():
        values = [v.lower().strip() for v in values]
        vidsToProcess = [(sessKey, vid) for (sessKey, vid) in vidsToProcess if coding[sessKey][criterion].lower().strip() in values]

    # Separate list into batches; break off a batch whenever length exceeds
    # batchLengthMinutes
    batches = []
    batchDurations = []
    currentBatch = []
    currentBatchLen = 0
    for (sessKey, vid) in vidsToProcess:
        dur = videoData[vid]['mp4Dur_trimmed']
        currentBatch.append((sessKey, vid, dur))
        currentBatchLen += dur
        if currentBatchLen > batchLengthMinutes * 60:
            batches.append(currentBatch)
            batchDurations.append(currentBatchLen)
            currentBatch = []
            currentBatchLen = 0
    # If anything's left in the last batch, include it
    if len(currentBatch):
        if includeIncompleteBatches:
            batches.append(currentBatch)
            batchDurations.append(currentBatchLen)
        else:
            warn('Some videos not being batched because they are not long enough for a complete batch')

    for [iBatch, batchList] in enumerate(batches):
        # Name the batch file
        done = False
        while not done:
            concatFilename = expId + '_' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)) + '.mp4'
            done = concatFilename not in paths.get_batchfiles()
        concatPath = os.path.join(paths.BATCH_DIR, concatFilename)
        print concatPath

        # Get full paths to videos
        batchPaths = [os.path.join(paths.SESSION_DIR, videoData[vid]['mp4Path_trimmed']) for (sessKey, vid) in batchList]

        # Create the batch file
        batchDur = concat_mp4s(concatPath, batchPaths)

        print "Batch duration -- actual: {}, expected: {}".format(batchDur, batchDurations[iBatch])
        durDiff = batchDur - batchDurations[iBatch]
        if durDiff > 0.033: # Greater than one frame at 30fps
            warn('Difference between predicted and actual batch length, batch filename {}'.format(concatFilename))

        # Add the batch to the videoData file
        add_batch(expId, concatFilename, batchList)






def add_batch(expId, batchFilename, videos):
    '''Add a batched video to data files.

    expId: experiment id, string
        (ex.: 574db6fa3de08a005bb8f844)
    batchFilename: filename of batch video file within batch dir (not full path)
    videos: ordered list of (sessionId, videoFilename, duration) tuples.
        sessionId is an index into the coding directory, videoFilename
        is the individual filename (not full path).

    The batch data file for this experiment will be updated to include this
    batch (see bat definition) and the videoData for all included videos will
    be updated with their positions within this batch:
    videoData[videoname]['inBatches'][batId] = iVid (index in this batch) '''

    # Load existing batch data & video data
    batches = load_batch_data(expId)
    videoData = load_video_data()

    # Create a batch dict for this batch
    bat = { 'batchFile': batchFilename,
            'videos': videos,
            'codedBy': [] }

    # Add this batch to the existing batches
    batId = uuid.uuid4().hex
    batches[batId] = bat


    # Add references to this batch in each videoData record affected
    for (iVid, (sessionId, videoname, dur)) in enumerate(videos):
        videoData[videoname]['inBatches'][batId] = iVid

    # Save batch and video data
    backup_and_save(paths.batch_filename(expId), batches)
    backup_and_save(paths.VIDEO_FILENAME, videoData)

def batch_id_for_filename(expId, batchFilename):
    '''Returns the batch ID for a given experiment & batch filename.'''

    batches = load_batch_data(expId)
    if not len(batchFilename):
        raise ValueError('remove_batch: must provide either batchId or batchFilename')
    for id in batches.keys():
        if batches[id]['batchFile'] == batchFilename:
            return id
    raise ValueError('remove_batch: no batch found for filename {}'.format(batchFilename))

def remove_batch(expId, batchId='', batchFilename='', deleteVideos=False):
    '''Remove a batched video from the data files (batch and video data).

    Either batchId or batchFilename must be provided. batchId is the ID used as a key in the batch data file for this experiment; batchFilename is the filename within the batch directory. If both are provided, only batchId is used.

    If batchId is 'all', all batches for this study are removed from the batch and video data files.

    deleteVideos (default false): whether to remove the specified batch videos in the batch dir as well as records of them

    Batch data will be removed from the batch file for this experiment and
    from each included video in videoData.'''

    # Load existing batch & video data
    batches = load_batch_data(expId)
    videoData = load_video_data()

    # First handle special case of removing all batches for this experiment
    if batchId == 'all':
        # Remove references to batches in all videoData for this study
        for (vid, vidData) in videoData.items():
            vidExpId = paths.parse_videoname(vid)[0]
            if vidExpId == expId:
                videoData[vid]['inBatches'] = {}
        backup_and_save(paths.VIDEO_FILENAME, videoData)
        # Empty batch data file
        backup_and_save(paths.batch_filename(expId), {})
        # Remove batch videos
        if deleteVideos:
            for batchVideoname in paths.get_batchfiles():
                vidExpId = batchVideoname.split('_')[0]
                if vidExpId == expId:
                    sp.call('rm ' + os.path.join(paths.BATCH_DIR, batchVideoname), shell=True)

        return

    # Use filename if provided instead of batchId
    if not len(batchId):
        batchId = batch_id_for_filename(expId, batchFilename)

    # Remove this batch from batch data
    videos = batches[batchId]['videos']
    vidName = batches[batchId]['batchFile']
    del batches[batchId]

    # Remove references to this batch in each videoData record affected
    for (iVid, (sessionId, videoname, dur)) in enumerate(videos):
        del videoData[videoname]['inBatches'][batchId]

    # Backup and save batch and video data
    backup_and_save(paths.batch_filename(expId), batches)
    backup_and_save(paths.VIDEO_FILENAME, videoData)
    print 'Removed batch from batch and video data'

    # Delete video
    if deleteVideos:
        batchPath = os.path.join(paths.BATCH_DIR, vidName)
        if os.path.exists(batchPath):
            sp.call('rm ' + batchPath, shell=True)
            print 'Deleted batch video'

def get_batch_info(expId='', batchId='', batchFilename=''):
    '''Given either a batchId or batch filename, return batch data for this
    batch. Must supply either expId or batchFilename.

    Returns the dictionary associated with this batch, with field:
        batchFile - filename of batch, within BATCH_DIR
        videos - list of (sessionKey, videoFilename, duration) tuples in order
            videos appear in batch
        codedBy - list of coders who have coded this batch

    '''

    # Load the batch data for this experiment
    if len(expId):
        batches = load_batch_data(expId)
    elif len('batchFilename'):
        expId = batchFilename.split('_')[0]
        batches = load_batch_data(expId)
    else:
        raise ValueError('get_batch_info: must supply either batchFilename or expId')

    # Use filename if provided instead of batchId
    if not len(batchId):
        batchId = batch_id_for_filename(expId, batchFilename)

    return batches[batchId]

def coderFields():
    '''Return a list of coder-specific fields to create/expect in coding data

    If FIELDNAME is one of these fields, then codingrecord[FIELDNAME] is a dictionary with keys = coder names.
    '''
    return ['coderComments']

def empty_coding_record():
    '''Return a new instance of an empty coding dict'''
    emptyRecord = {'consent': 'orig',
            'usable': '',
            'feedback': '',
            'videosExpected': [],
            'videosFound': []}
    for field in coderFields():
        emptyRecord[field] = {} # CoderName: 'comment'
    return emptyRecord

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

    backup_and_save(paths.coding_filename(expId), coding)


    if display:
        printer.pprint(coding)

    print "Updated coding with {} new records for experiment: {}".format(len(newCoding), expId)




def export_accounts():
    '''Create a .csv sheet showing all account data.

    All fields except password and profiles will be included. Instead of the list of child profile dicts under 'profiles', the individual dicts will be expanded as child[N].[fieldname] with N starting at 0.
    '''
    accountsRaw = load_account_data();
    print "loaded account data"
    accs = []
    headers = set()
    allheaders = set()
    for (userid, acc) in accountsRaw.items():
        thisAcc = acc['attributes']
        thisAcc['username'] = userid
        profiles = thisAcc['profiles']
        del thisAcc['profiles']
        del thisAcc['password']
        headers = headers | set(thisAcc.keys())
        iCh = 0
        for pr in profiles:
            for (k,v) in pr.items():
                thisAcc['child' + str(iCh) + '.' + k] = v
            iCh += 1
        for k in thisAcc.keys():
            if type(thisAcc[k]) is unicode:
                thisAcc[k] = thisAcc[k].encode('utf-8')
        accs.append(thisAcc)
        allheaders = allheaders | set(thisAcc.keys())

    # Order headers in the file: initial list, then regular, then child-profile
    initialHeaders = [u'username']
    childHeaders = allheaders - headers
    headers = list(headers - set(initialHeaders))
    headers.sort()
    childHeaders = list(childHeaders)
    childHeaders.sort()
    headerList = initialHeaders + headers + childHeaders
    headerList = [h.encode('utf-8') for h in headerList]

    # Back up any existing accounts csv file by the same name
    accountsheetPath = paths.accountsheet_filename()
    backup_and_save_dict(accountsheetPath, accs, headerList)

def generate_codesheet(expId, coderName, showOtherCoders=True, showAllHeaders=False, includeFields=[], filter={}):
    '''Create a .csv coding sheet for a particular study and coder

    csv will be named expID_coderName.csv and live in the CODING_DIR.

    expId: experiment id

    coderName: name of coder; must be in paths.CODERS. Use 'all' to show all coders.

    showOtherCoders: boolean, whether to display columns for other coders' coder-specific data

    showAllHeaders: boolean, whether to include all headers or only the basics

    includeFields: list of field ENDINGS to include beyond basic headers. For each session, any field ENDING in a string in this list will be included. The original field name will be removed and the corresponding data stored under this partial name, so they should be unique endings within sessions. (Using just the ending allows for variation in which segment the field is associated with.)

    filter: dictionary of header:value pairs that should be required in order for the session to be included in the codesheet. (Most common usage is {'consent':'yes'} to show only records we have already confirmed consent for.)

    '''

    # Load all necessary information
    coding = load_coding(expId)
    sessions = load_session_data(expId)
    accounts = load_account_data()

    if coderName != 'all' and coderName not in paths.CODERS:
        raise ValueError('Unknown coder name', coderName)

    # Make coding into a list instead of dict
    codingList = []
    headers = set() # Keep track of all headers

    for (key,val) in coding.items():
        # Get session information for this coding session
        sess = find_session(sessions, key)

        # Combine coding & session data
        val = flatten_dict(val)
        sess = flatten_dict(sess)
        val.update(sess)

        # Find which account/child this session is associated with
        profile = val['attributes.profileId']
        pieces = profile.split('.')
        username = pieces[0]
        child = pieces[1]

        # Get the associated account data and add it to the session
        acc = accounts[username]
        childData = [pr for pr in acc['attributes']['profiles'] if pr['profileId']==profile]
        childDataLabeled = {}
        for (k,v) in childData[0].items():
            childDataLabeled['child.' + k] = v
        val.update(childDataLabeled)

        # Look for fields that end in any of the suffixes in includeFields.
        # If one is found, move the data from that field to the corresponding
        # member of includeFields.
        for fieldEnd in includeFields:
            for field in val.keys():
                if field[-len(fieldEnd):] == fieldEnd:
                    val[fieldEnd] = val[field]
                    del val[field]

        # Add any new headers from this session
        headers = headers | set(val.keys())

        codingList.append(val)

    # Organize the headers we actually want to put in the file - headerStart will come first, then alphabetized other headers if we're using them
    headerStart = ['id', 'meta.created-on', 'child.profileId', 'consent', 'usable', 'feedback']

    # Insert this and other coders' data here if using
    if coderName == 'all':
        for field in coderFields():
            headerStart = headerStart + [h for h in headers if h[:len(field + '.')] == field + '.']
    else:
        for field in coderFields():
            headerStart = headerStart + [field + '.' + coderName]
            if showOtherCoders:
                headerStart = headerStart + [h for h in headers if h[:len(field + '.')] == field + '.' and h != field + '.' + coderName]

    # Continue predetermined starting list
    headerStart = headerStart + ['attributes.feedback',
        'attributes.hasReadFeedback',
        'attributes.completed', 'videosExpected', 'videosFound',
        'child.birthday', 'child.deleted', 'child.gender', 'child.profileId',
        'child.additionalInformation'] + includeFields

    # Add remaining headers from data if using
    if showAllHeaders:
        headerList = list(headers - set(headerStart))
        headerList.sort()
        headerList = headerStart + headerList
    else:
        headerList = headerStart



    for (key, val) in filter.items():
        codingList = [sess for sess in codingList if key in sess.keys() and sess[key]==val]


    for record in codingList:
        for k in record.keys():
            if type(record[k]) is unicode:
                record[k] = record[k].encode('utf-8')

    # Back up any existing coding file by the same name & save
    codesheetPath = paths.codesheet_filename(expId, coderName)
    backup_and_save_dict(codesheetPath, codingList, headerList)

def commit_coding(expId, coderName):
    '''Update the coding file for expId based on a CSV edited by a coder.

    Raises IOError if the CSV file is not found.

    Session keys are used to match CSV to pickled data records. Only coder fields for this coder (fields in coderFields() + .[coderName]) are updated.

    Fields are only *added* to coding records if there is a nonempty value to place. Fields are *updated* in all cases (even to an empty value).'''

    # Fetch coding information: data, path to CSV, and which coder fields
    coding = load_coding(expId)
    codesheetPath = paths.codesheet_filename(expId, coderName)
    thisCoderFields = [f + '.' + coderName for f in coderFields()]

    if not os.path.exists(codesheetPath):
        raise IOError('Coding sheet not found: {}'.format(codesheetPath))

    # Read each row of the coder CSV. 'rU' is important for Mac-formatted CSVs
    # saved in Excel.
    with open(codesheetPath, 'rU') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            id = row['id']
            if id in coding.keys(): # Match to a sessionKey in the coding dict.
                # Go through each expected coder-specific field, e.g.
                # coderComments
                for field in thisCoderFields:
                    if field in row.keys():
                        # Parse the CSV field name. It's been flattened, so what
                        # would be ...[fieldName][coderName] is now
                        # fieldName.coderName. Using this for more generalizability
                        # later if we want to be able to edit other coder names in
                        # addition--can manipulate thisCoderFields.
                        fieldParts = field.split('.')
                        if len(fieldParts) != 2:
                            warn('Bad coder field name {}, should be of the form GeneralField.CoderName'.format(field))
                            continue
                        genField, coderField = fieldParts

                        # Field isn't already there
                        if genField not in coding[id].keys() or coderField not in coding[id][genField].keys():
                            if len(row[field]):
                                print('Adding field {} to session {}: "{}"'.format(field, id, row[field]))
                                coding[id][genField][coderField] = row[field]

                        # Field is already there and this value is new
                        elif coding[id][genField][coderField] != row[field]:
                            print('Updating field {} in session {}: "{}" ->  "{}"'.format(field, id, coding[id][genField][coderField], row[field]))
                            coding[id][genField][coderField] = row[field]
                    else:
                        warn('Missing expected row header in coding CSV: {}'.format(field))
            else: # Couldn't find this sessionKey in the coding dict.
                warn('ID found in coding CSV but not in coding file, ignoring: {}'.format(id))

    # Actually save coding
    backup_and_save(paths.coding_filename(expId), coding)

def commit_global(expId, coderName, commitFields):
    '''Update the coding file for expId based on a CSV edited by a coder;
    edit global fields like consent/usable rather than coder-specific fields.

    expId: experiment id, string
        (ex.: 574db6fa3de08a005bb8f844)

    coderName: name of coder to use CSV file from. Raises IOError if the CSV
        file is not found.

    commitFields: list of headers to commit.

    Session keys are used to match CSV to pickled data records. Fields are
    updated in all cases (even to an empty value).'''

    # Fetch coding information: data, path to CSV, and which coder fields
    coding = load_coding(expId)
    codesheetPath = paths.codesheet_filename(expId, coderName)

    if not os.path.exists(codesheetPath):
        raise IOError('Coding sheet not found: {}'.format(codesheetPath))

    # Read each row of the coder CSV. 'rU' is important for Mac-formatted CSVs
    # saved in Excel.
    with open(codesheetPath, 'rU') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            id = row['id']
            if id in coding.keys(): # Match to a sessionKey in the coding dict.
                for field in commitFields:
                    if field not in row.keys():
                        raise ValueError('Bad commitField name, not found in CSV')

                    if field not in coding[id].keys():
                        print 'Adding field {} to session {}: "{}"'.format(field, id, row[field])
                    elif row[field] != coding[id][field]:
                        print 'Updating field {} for session {}: "{}" to "{}"'.format(field, id, coding[id][field], row[field])
                    coding[id][field] = row[field]

            else: # Couldn't find this sessionKey in the coding dict.
                warn('ID found in coding CSV but not in coding file, ignoring: {}'.format(id))

    # Actually save coding
    backup_and_save(paths.coding_filename(expId), coding)

def send_feedback(expId):
    '''Send feedback back to JamDB to show to participants from coding data.

    First updates session data from server so we know what feedback is new.

    Does not update feedback based on a coder CSV - need to first run
    commit_global(expId, coderName, ['feedback']) to save feedback to the
    coding file.

    '''

    # Fetch coding information: data, path to CSV, and which coder fields
    coding = load_coding(expId)

    # Update session data
    update_session_data(expId)
    sessData = load_session_data(expId)

    # Set up connection to JamDB
    client = ExperimenterClient(access_token=paths.OSF_ACCESS_TOKEN).authenticate()

    # For each session, look at old and new feedback; update if needed
    for sessKey in coding.keys():

        thisSession = find_session(sessData, sessKey)
        existingFeedback = thisSession['attributes']['feedback']

        newFeedback = coding[sessKey]['feedback']

        if newFeedback != existingFeedback:
            print 'Updating feedback for session {}. Existing: {}, new: {}'.format(sessKey, existingFeedback, newFeedback)
            client.set_session_feedback({'id': sessKey}, newFeedback)

    print "Sent updated feedback to server for exp {}".format(expId)



if __name__ == '__main__':

    physID = '57a212f23de08a003c10c6cb'
    testID = '57a0e5723de08a003c0fdd8e' # test study for audrey

    IDs = [testID]

    includeFields = ['exit-survey.formData.withdraw',
        'exit-survey.formData.databrary',
        'exit-survey.formData.privacy',
        'exit-survey.formData.birthdate',
        'pref-phys-videos.whichObjects',
        'pref-phys-videos.startType',
        'pref-phys-videos.showStay',
        'pref-phys-videos.NPERTYPE',
        'mood-survey.lastEat',
        'mood-survey.doingBefore',
        'mood-survey.napWakeUp',
        'mood-survey.usualNapSchedule',
        'mood-survey.nextNap',
        'mood-survey.rested',
        'mood-survey.healthy',
        'mood-survey.childHappy',
        'mood-survey.active',
        'mood-survey.energetic',
        'mood-survey.ontopofstuff',
        'mood-survey.parentHappy']

    cmds = sys.argv[1:]

    if 'doUpdate' in cmds:
        print 'Starting Lookit update, {:%Y-%m-%d%H:%M:%S}'.format(datetime.datetime.now())

        id = sys.argv[2]

        DISP = True
        update_session_data(id, display=DISP)
        update_coding(id, display=DISP)
        #newVideos = sync_S3(pull=True)
        #sessionsAffected, improperFilenames, unmatched = update_video_data(whichStudies=[id], reprocess=False, resetPaths=False, display=DISP)
        #assert len(unmatched) == 0
        #update_videos_found(id)
        #concatenate_session_videos(id, 'all', display=True, replace=False)
        #make_mp4s_for_study(id, sessionsToProcess='missing', display=True, trimming=5, suffix='trimmed')
        #batch_videos(id, batchLengthMinutes=5, codingCriteria={'consent':['orig'], 'usable':['']})
        #update_account_data()
        #export_accounts()
        generate_codesheet(id, 'Kim', showAllHeaders=True)
        #commit_coding(id, 'Kim')

        print "done!"

    elif 'getVideos' in cmds:
        newVideos=sync_S3(pull=True)

    elif 'testAccounts' in cmds:
        #update_account_data()
        export_accounts()

    elif 'testBatch' in cmds:
        studyID = testID
        update_coding(studyID, display=True)
        update_videos_found(studyID)
        make_mp4s_for_study(studyID, sessionsToProcess='missing', display=True, trimming=20, suffix='trimmed')
        batch_videos(studyID, batchLengthMinutes=5, codingCriteria={'consent':['orig'], 'usable':['']})

    elif 'fetch' in cmds:
        id = sys.argv[2]
        update_session_data(id, display=False)
        update_coding(id)
        generate_codesheet(id, 'Kim', includeFields=includeFields)

    elif 'commit' in cmds:
        id = sys.argv[2]
        commit_coding(id, 'Kim')
        commit_global(id, 'Kim', ['consent', 'feedback'])

    elif 'testRemoveBatch' in cmds:
        remove_batch(testID, batchId='all', batchFilename='', deleteVideos=True)

    elif 'testFeedback' in cmds:
        id = sys.argv[2]
        send_feedback(id)

    elif 'getBatchData' in cmds:
        batchFilename = sys.argv[2]
        printer.pprint(get_batch_info(batchFilename=batchFilename))
