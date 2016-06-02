import os
import errno
import subprocess as sp
from sets import Set
#import xlrd
#import xlwt
#from xlutils.copy import copy as xlcopy
import warnings
import numpy as np
import re
import shlex
import json

# function to find the resolution of the input video file
# http://stackoverflow.com/a/34356719
def findVideoResolution(pathToInputVideo):
	cmd = "ffprobe -v quiet -print_format json -show_streams"
	args = shlex.split(cmd)
	args.append(pathToInputVideo)
	# run the ffprobe process, decode stdout into utf-8 & convert to JSON
	ffprobeOutput = sp.check_output(args).decode('utf-8')
	ffprobeOutput = json.loads(ffprobeOutput)

	# find height and width
	height = ffprobeOutput['streams'][0]['height']
	width = ffprobeOutput['streams'][0]['width']

	return height, width

def get_framerate(vidName, threshold):
	'''Get approximate frame count and duration of streamed video clip.

	vidName: path to video file (any format ffmpeg understands should be fine)
	dims: dimensions of video frame as a tuple (e.g. (640,480,3))
	threshold: what fraction of pixels in a frame need to change at all
		in order to count this as a new frame

	returns (frameCount, duration) where frameCount is how many "pretty distinct" frames
	there are (float) and duration is in seconds.'''
	vidPath = os.path.join(os.environ.get('VIDEO_DIR'), vidName)
	(h,w) = findVideoResolution(vidPath)
	dims = [h,w,3]

	nPixReq = dims[0] * dims[1] * threshold

	# Get the duration of the clip using ffprobe
	p1 = sp.Popen(['ffprobe', '-i', vidPath,
					'-show_format', '-v', 'quiet'], stdout=sp.PIPE, stderr=sp.STDOUT)
	output = p1.communicate()[0]
	print output
	duration = float(re.search(r"duration=(.*)\n", output).group(1))

	# Now get ready to loop through the frames, reading in each one using ffmpeg
	command = [ 'ffmpeg', '-i', vidPath,
				'-f', 'image2pipe',
				'-pix_fmt', 'rgb24',
				'-vcodec', 'rawvideo', '-', '-loglevel', 'fatal']
	pipe = sp.Popen(command, stdout = sp.PIPE, stderr=sp.PIPE, bufsize=10**8)

	lastFrame = np.zeros(dims,dtype='uint8')
	frameCount = 1
	while True:
		raw_image = pipe.stdout.read(int(dims[0]*dims[1]*dims[2]))
		# transform the byte read into a numpy array
		frame = np.fromstring(raw_image, dtype='uint8')
		if len(frame) == 0:
			break;

		frame = frame.reshape(dims)
		pipe.stdout.flush()

		pixDiff = np.sum(frame-lastFrame, axis=2)
		numNew = np.sum(pixDiff > 3)
		if numNew > nPixReq:
			frameCount += 1
			lastFrame = frame

	frameCount = float(frameCount)
	return (frameCount, duration, dims)

def add_data(findDict, dataDict, labels, sheet, sheetW):
	''' Add data to a spreadsheet.

	findDict: the query, e.g. {'userid':2345, 'recordingSet':'W4gH7u'}
		or the row of the spreadsheet
	dataDict: labels and data to add, e.g. {'newField':'valueforthisguy', ...}
	nrows:
	labels: current labels of this spreadsheet (col headers)
	sheet: ref to sheet

	Writes to spreadsheet if it finds exactly one match.
	returns (labels, status).
		status 0: okay, added data to one row
		status -1: no matches
		status -2: more than one match
	Labels will be updated if needed.'''

	matches = range(1, sheet.nrows)


	if type(findDict) == type({}):
		for k in findDict.keys():
			theseVals = sheet.col_values(labels.index(k))
			if type(findDict[k]) == type('s'):
				matches = [i for i, x in enumerate(theseVals) if ((findDict[k] in [ str(x), '\"'+str(x)+'\"']) or (('\"' + findDict[k] + '\"') == str(x))) and i in matches]
			else:
				matches = [i for i, x in enumerate(theseVals) if findDict[k] == x and i in matches]

		if len(matches) == 0:
			print 'no matches found: ', findDict
			return (labels, -1)
		elif len(matches) > 1:
			print 'multiple matches found: ', findDict
			return (labels, -2)

		m = matches[0]
	else:
		m = findDict


	for k in dataDict.keys():
		if k not in labels:
			sheetW.write(0, len(labels), k)
			labels = labels + [k]
		sheetW.write(m, labels.index(k), dataDict[k])

	return (labels, 0)

def parse_lookit_filename(filename):
	pieces = filename.split('_')

	videonumber = pieces[-1]
	privacy		= pieces[-2]
	child		= pieces[-3]
	session		= pieces[-4]
	family		= pieces[-5]
	study		= pieces[1]

	return (study, family, child, session, privacy, videonumber)
#
#
#
# dirname = '/Volumes/NovelToy2/VideoClips/Lookit/'
#
# # For Snapbeads & BabyGolf
# if not os.path.isdir(dirname):
#	dirname = '/Volumes/NovelToy2-1/VideoClips/Lookit/'
#
# EXT = '.flv'
# ALLEXT = ['.flv', '.mp4']
# WITHDRAWNEXT = ['.flv--WITHDRAWN', '.mp4--WITHDRAWN']
#
# paths = Set([])
#
# # First look through consent directories and put away any videos that are labeled CONSENT or NOCONSENT
# for f in os.listdir(dirname):
#	if os.path.isdir(os.path.join(dirname, f)):
#		consentdir = os.path.join(dirname, f, 'consent')
#		if os.path.exists(consentdir):
#			print 'Checking consent directory: ' + consentdir
#			if not(os.path.exists(os.path.join(consentdir, 'consent_yes'))):
#				os.makedirs(os.path.join(consentdir, 'consent_yes'))
#			if not(os.path.exists(os.path.join(consentdir, 'consent_no'))):
#				os.makedirs(os.path.join(consentdir, 'consent_no'))
#
#			for f in os.listdir(consentdir):
#				if not(os.path.isdir(os.path.join(consentdir, f))) and f[0] != '.' and f[-3:] != 'txt':
#					(_,_,_,_,_,label) = parse_lookit_filename(f)
#					if label == 'CONSENT.flv' or label == 'CONSENT.mp4':
#						os.rename(os.path.join(consentdir, f), os.path.join(consentdir, 'consent_yes', f))
#					elif label == 'NOCONSENT':
#						os.rename(os.path.join(consentdir, f), os.path.join(consentdir, 'consent_no', f))
#
#
# # Find all the files in the main lookit video directory and put them in their spots if
# # they're new; make labeled FLV files
# for f in os.listdir(dirname):
#	if not(os.path.isdir(os.path.join(dirname, f))):
#		(shortname, ext) = os.path.splitext(f)
#		if ext in ALLEXT or ext in WITHDRAWNEXT:
#			(study, fam, ch, sess, priv, num) = parse_lookit_filename(shortname)
#			print (study, fam, ch, sess, priv, num)
#			if num=='0':
#				p = os.path.join(dirname, study, 'consent')
#			else: # Figure out where it should go and add to the list of paths to process.
#				p = os.path.join(dirname, study, fam+ch, sess)
#
#			# For both consent and study videos, check whether we already have the same
#			# filename (up to privacy level which can vary because the videos start off as
#			# 'INCOMPLETE' and are sometimes re-sent from Wowza later.
#			haveFile = False
#			if os.path.isdir(p):
#				# Traverse directory, because consent files may have been moved to consent_yes or consent_no
#				for thisDir, subdirList, fileList in os.walk(p):
#					for existingFile in fileList:
#						(shortExistingName, existingExt) = os.path.splitext(existingFile)
#						if (existingExt in ALLEXT and str.isdigit(shortExistingName[-1])) or \
#							existingExt in WITHDRAWNEXT or shortExistingName[-7:]=='CONSENT':
#							(eS, eF, eC, eSess, eP, eN) = parse_lookit_filename(shortExistingName)
#							if (num=='0' and eS==study and eF==fam and eC==ch and eSess==sess) or\
#								(num!='0' and eN==num):
#								haveFile = True
#								break
#
#			if haveFile: # Move both extra consent and extra study videos here
#				print 'duplicate file ' + shortname
#				p = os.path.join(dirname, 'DUPLICATE VIDEOS')
#			else:
#				print 'not a duplicate file ' + shortname
#
#			if not(num=='0') and not(haveFile):
#				# If we already have this one, don't add to paths for further processing;
#				# just move the video to the duplicates directory
#				paths.add(p)
#
#			new = make_sure_path_exists(p)
#
#			filename = os.path.join(p, f)
#			# Actually move the file to its new home
#			os.rename(os.path.join(dirname, f), filename)
#
#
# consent_path = '/Volumes/NovelToy2/CurrentProjects/Lookit/Consent/'
#
# print 'making combined files and cleaning up--paths to process:'
# print paths
#
# # Then make the combined files and clean up
# for p in paths:
#
#	filepath = os.path.join(p, "filelist.txt")
#	# Clear any existing filelist.txt
#	sp.call(["rm", filepath])
#
#	# First make each labeled flv segment (1.flv, etc.) and build up the filelist.
#	for fname in os.listdir(p):
#		(shortname, ext) = os.path.splitext(fname)
#		if ext in ALLEXT and str.isdigit(shortname[-1]):
#			(study, fam, ch, sess, priv, num) = parse_lookit_filename(shortname)
#			filename = os.path.join(p, fname)
#			sp.call(["ffmpeg", "-i", filename, "-ar", "22050", "-q:v", "1", "-vf", "drawtext='fontfile=/Library/Fonts/Arial Black.ttf:text=\'"+str(num)+"\':fontsize=20:fontcolor=red:x=20:y=40'", os.path.join(p, num+EXT)])
#			f = open(filepath, "a")
#			f.write("file " + os.path.join(p,num+EXT) + "\n")
#			f.close()
#
#			# Add framerate and duration of this video to the consent spreadsheet
#			(framecount, dur) = get_framerate(os.path.join(p,fname), (640,480,3), 0.2)
#			framerate = framecount / dur
#
#			if all(char in	'-0123456789' for char in fam):
#				famNum = int(fam)
#			findDict = {'user_id':famNum, 'recordingSet':sess}
#
#			if study == 'speech':
#				xlsName = 'consent_speech_match.xls'
#			else:
#				xlsName = 'consent_' + study + '.xls'
#
#			consentXls = os.path.join(consent_path, xlsName)
#			consentbook = xlrd.open_workbook(consentXls, formatting_info=True)
#			consentsheet = consentbook.sheet_by_index(0)
#			#assert(consentsheet.cell(0,DBID_COL).value == 'DBID')
#			#assert(consentsheet.cell(0,CONSENT_COL).value == 'consent')
#			consentlabels = consentsheet.row_values(0)
#			consentbookW = xlcopy(consentbook)
#			consentsheetW = consentbookW.get_sheet(0)
#
#			(consentlabels, status) = add_data(findDict, {'hasVideo':'yes'}, consentlabels, consentsheet, consentsheetW)
#			(consentlabels, status) = add_data(findDict, {'fps-'+str(num):framerate},  consentlabels, consentsheet, consentsheetW)
#			(consentlabels, status) = add_data(findDict, {'dur-'+str(num):dur},	 consentlabels, consentsheet, consentsheetW)
#			consentbookW.save(consentXls)
#
#			print 'Framerate, duration: ', (framerate, dur)
#
#	if os.path.exists(filepath):
#
#		# Decide how to name the combined file
#		combinedfilename = study + '_' + fam + '_' + ch + '_' + sess + '_' + priv + '.mp4'
#
#		# Concatenate the labeled video files
#		sp.call(["ffmpeg", "-f", "concat", "-i", os.path.join(p, "filelist.txt"), "-vcodec", "libx264", os.path.join(p, combinedfilename)])
#
#		# Clean up the temporary files (NN.flv, on list)
#		with open(filepath, 'r') as f:
#			for line in f:
#				words = line.split()
#				sp.call(["rm", words[1]])
#
#
