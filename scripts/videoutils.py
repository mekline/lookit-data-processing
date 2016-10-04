import os
import subprocess as sp
from warnings import warn
import shlex
import json
import lookitpaths as paths

# function to find the resolution of the input video file
# http://stackoverflow.com/a/34356719
def get_video_details(vidName, whichAttr, fullpath=False):
    '''Uses ffprobe to retrieve details about a video.

    get_video_details(vidName, whichAttr, fullpath=False)

    vidName: video filename. Assumed to be in VIDEO_DIR unless
        fullpath is True, in which case vidName should be the full path to the
        video file.

    whichAttr: single attribute or list of attributes to retrieve. Options are:
        duration - duration of video in seconds
        bitrate - bit rate of video
        starttime - start time of video
        [All options below require a video stream; will warn and return 0 if
        no video stream is available]
        height - height in pixels
        width - width in pixels
        nframes - number of frames
        vidduration - duration of video stream in seconds
        audduration - duration of audio stream in seconds

        Returns a single value if whichAttr is a string, or a list of values
        corresponding to those requested if whichAttr is a list of strings.
        '''

    # Ensure whichAttr is a list
    if isinstance(whichAttr, str):
        whichAttr = [whichAttr]

    # Get full path to video
    if not(fullpath):
        vidPath = os.path.join(paths.VIDEO_DIR, vidName)
    else:
        vidPath = vidName

    # Run ffprobe and collect output with data about video
    cmd = paths.FFPROBE + " -v quiet -show_format -print_format json -show_streams -count_frames"
    args = shlex.split(cmd)
    args.append(vidPath)
    try:
        ffprobeOutput = sp.check_output(args).decode('utf-8')
    except:
        warn('Error running ffprobe command {} to get video details about {}, returning -1'.format(' '.join(args), vidName))
        if len(whichAttr) == 1:
            return -1
        else:
            return [-1] * len(whichAttr)

    ffprobeOutput = json.loads(ffprobeOutput)


    # Loop through attributes and collect specific information
    attributes = []
    for attr in whichAttr:
        returnVal = -1
        if attr == 'duration':
            returnVal = float(ffprobeOutput['format']['duration'])
        elif attr == 'bitrate':
            returnVal = float(ffprobeOutput['format']['bit_rate'])
        elif attr == 'starttime':
            returnVal = float(ffprobeOutput['format']['start_time'])
        # Attributes that require a video/audio stream...
        elif attr in ['nframes', 'height', 'width', 'vidduration', 'audduration']:
            audioStream = -1
            videoStream = -1
            for iStream in range(len(ffprobeOutput['streams'])):
                if ffprobeOutput['streams'][iStream]['codec_type'] == 'audio':
                    audioStream = iStream
                elif ffprobeOutput['streams'][iStream]['codec_type'] == 'video':
                    videoStream = iStream


            if videoStream == -1:
                warn('Missing video stream for video {}'.format(vidName))
                if attr in ['nframes', 'height', 'width', 'vidduration']:
                    returnVal = 0
                    attributes.append(returnVal)
                    continue

            if audioStream == -1:
                warn('Missing audio stream for video {}'.format(vidName))
                if attr in ['audduration']:
                    returnVal = 0
                    attributes.append(returnVal)
                    continue

            if attr == 'nframes':
                if 'nb_read_frames' in ffprobeOutput['streams'][videoStream].keys():
                    returnVal = float(ffprobeOutput['streams'][videoStream]['nb_read_frames'])
                else:
                    returnVal = 0
                    warn('No frame data for {}'.format(vidName))
            elif attr == 'width':
                returnVal = float(ffprobeOutput['streams'][videoStream]['width'])
            elif attr == 'height':
                returnVal = float(ffprobeOutput['streams'][videoStream]['height'])
            elif attr == 'vidduration':
                returnVal = float(ffprobeOutput['streams'][videoStream]['duration'])
            elif attr == 'audduration':
                returnVal = float(ffprobeOutput['streams'][audioStream]['duration'])
        else:
            raise ValueError('Unrecognized attribute requested')
        attributes.append(returnVal)

    # Return just a string if there's only one return value in the list
    if len(attributes) == 1:
        attributes = attributes[0]

    return attributes


# def add_data(findDict, dataDict, labels, sheet, sheetW):
# 	''' Add data to a spreadsheet.
#
# 	findDict: the query, e.g. {'userid':2345, 'recordingSet':'W4gH7u'}
# 		or the row of the spreadsheet
# 	dataDict: labels and data to add, e.g. {'newField':'valueforthisguy', ...}
# 	nrows:
# 	labels: current labels of this spreadsheet (col headers)
# 	sheet: ref to sheet
#
# 	Writes to spreadsheet if it finds exactly one match.
# 	returns (labels, status).
# 		status 0: okay, added data to one row
# 		status -1: no matches
# 		status -2: more than one match
# 	Labels will be updated if needed.'''
#
# 	matches = range(1, sheet.nrows)
#
#
# 	if type(findDict) == type({}):
# 		for k in findDict.keys():
# 			theseVals = sheet.col_values(labels.index(k))
# 			if type(findDict[k]) == type('s'):
# 				matches = [i for i, x in enumerate(theseVals) if ((findDict[k] in [ str(x), '\"'+str(x)+'\"']) or (('\"' + findDict[k] + '\"') == str(x))) and i in matches]
# 			else:
# 				matches = [i for i, x in enumerate(theseVals) if findDict[k] == x and i in matches]
#
# 		if len(matches) == 0:
# 			print 'no matches found: ', findDict
# 			return (labels, -1)
# 		elif len(matches) > 1:
# 			print 'multiple matches found: ', findDict
# 			return (labels, -2)
#
# 		m = matches[0]
# 	else:
# 		m = findDict
#
#
# 	for k in dataDict.keys():
# 		if k not in labels:
# 			sheetW.write(0, len(labels), k)
# 			labels = labels + [k]
# 		sheetW.write(m, labels.index(k), dataDict[k])
#
# 	return (labels, 0)
