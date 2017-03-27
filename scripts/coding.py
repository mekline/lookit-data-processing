import sysconfig
import os
import errno
import pickle
from client import Account, ExperimenterClient
#from sendgrid_client import SendGrid
from utils import make_sure_path_exists, indent, timestamp, printer, backup_and_save, flatten_dict, backup, backup_and_save_dict, display_unique_counts
import uuid
import subprocess as sp
import sys
import videoutils
import vcode
from warnings import warn
import datetime
import lookitpaths as paths
import conf
from updatefromlookit import sync_S3, pull_from_wowza, update_account_data, show_all_experiments, update_session_data
import csv
import random
import string
import argparse
import unittest
import numpy as np
import scipy.stats
if sysconfig.get_config_var("PYTHONFRAMEWORK"):
	import matplotlib.pyplot as plt
else:
	print "Non-framework build: not importing matplotlib. Plotting functionality will raise error."


class Experiment(object):
	'''Represent a Lookit experiment with stored session, coding, & video data.'''

	# Don't have ffmpeg tell us everything it has ever thought about.
	loglevel = 'error'

	# Coder-specific fields to create/expect in coding data. If FIELDNAME is one
	# of these fields, then codingrecord[FIELDNAME] is a dict with keys = coder
	# names. New fields will be added to coding records the next time coding is
	# updated. If an existing codesheet is committed before coding is updated OR a
	# new coder sheet is created, a warning will be displayed that an expected field is
	# missing.
	coderFields = ['coderComments']
	videoData = {}
	accounts = {}

	@classmethod
	def find_session(cls, sessionData, sessionKey):
		for sess in sessionData['sessions']:
			if sess['id'] == sessionKey:
				return sess
		return -1

	@classmethod
	def load_batch_data(cls, expId):
		'''Return saved batch data for this experiment. Empty if no data.'''
		batchFile = paths.batch_filename(expId)
		if os.path.exists(batchFile):
			with open(batchFile,'rb') as f:
				batches = pickle.load(f)
			return batches
		else:
			return {}

	@classmethod
	def load_session_data(cls, expId):
		'''Return saved session data for this experiment, or [] if none saved'''
		sessionFile = paths.session_filename(expId)
		if os.path.exists(sessionFile):
			with open(paths.session_filename(expId),'rb') as f:
				exp = pickle.load(f)
		else:
			exp = []
		return exp

	@classmethod
	def load_email_data(cls, expId):
		'''Return saved email data for this experiment, or {} if none saved'''
		emailFile = paths.email_filename(expId)
		if os.path.exists(emailFile):
			with open(paths.email_filename(expId),'rb') as f:
				email = pickle.load(f)
		else:
			email = {}
		return email

	@classmethod
	def load_coding(cls, expId):
		'''Return saved coding data for this experiment, or empty dict if none saved.'''
		codingFile = paths.coding_filename(expId)
		if os.path.exists(codingFile):
			with open(codingFile,'rb') as f:
				coding = pickle.load(f)
		else:
			coding = {}
		return coding

	@classmethod
	def load_video_data(cls):
		'''Return video data, or empty dict if none saved.'''
		if os.path.exists(paths.VIDEO_FILENAME):
			with open(paths.VIDEO_FILENAME,'rb') as f:
				videoData = pickle.load(f)
		else:
			videoData = {}
		cls.videoData = videoData
		return videoData

	@classmethod
	def load_account_data(cls):
		'''Return saved account data, or empty dict if none saved.'''
		if os.path.exists(paths.ACCOUNT_FILENAME):
			with open(paths.ACCOUNT_FILENAME,'rb') as f:
				accountData = pickle.load(f)
		else:
			accountData = {}
		cls.accounts = accountData
		return accountData

	@classmethod
	def make_mp4s(cls, sessDirRel, vidNames, display=False, trimming=False, suffix='', replace=False, whichFrames=[]):
		''' Convert flvs in VIDEO_DIR to mp4s organized in SESSION_DIR for a
		particular session

			sessDirRel: relative path to session directory where mp4s
				should be saved. mp4s will be created in
				paths.SESSION_DIR/sessDirRel.

			vidNames: list of video names (flv filenames within
				VIDEO_DIR, also keys into videoData) to convert

			display: whether to display information about progress

			trimming: False (default) not to do any trimming of video
				file, or a maximum clip duration in seconds. The last
				trimming seconds (counted from the end of the
				shortest stream--generally video rather than audio)
				will be kept, or if the video is shorter than
				trimming, the entire video will be kept.

			suffix: string to append to the mp4 filenames (they'll be
				named as their originating flv filenames, plus
				"_[suffix]") and to the fields 'mp4Path_[suffix]' and
				'mp4Dur_[suffix]' in videoData. Default ''.

			replace: False (default) to skip making an mp4 if (a) we
				already have the correct filename and (b) we have a
				record of it in videoData, True to make anyway.

			whichFrames: list of substrings of video filenames for which we should
				actually do processing, e.g. ['video-consent', 'video-preview'].
				Default of [] means process all frames.

			To make the mp4, we first create video-only and
				audio-only files from the original flv file. Then we
				put them together and delete the temporary files. The
				final mp4 has a duration equal to the length of the
				video stream (technically it has a duration equal to
				the shorter of the audio and video streams, but
				generally video is shorter, and we pad the audio
				stream with silence in case it's shorter). Trimming,
				however, is done (to the best of my understanding)
				from the end of the longest stream. This is
				appropriate since it is possible for audio to
				continue to the end of a recording period, while
				video gets cut off earlier due to the greater
				bandwidth required.

			mp4s have a text label in the top left that shows
				[segment]_[session]_[timestamp and randomstring] from
				the original flv name.

			Returns a dictionary with keys = vidNames. Each value is
				a dict with the following fields: 'mp4Dur_[suffix]':
				0 if no video was able to be created, due to missing
				video or a missing video stream. It is also possible
				for video not to be created if there is a video
				stream, but it stops and then the audio stream
				continues for at least trimming seconds after that.
				'mp4Path_[suffix]': Relative path (from
				paths.SESSION_DIR) to mp4 created, or '' if as above
				mp4 was not created.

			(Does NOT save anything directly to videoData, since this
				may be called many times in short succession!)'''


		vidData = {}
		concat = [paths.FFMPEG]

		# Get full path to the session directory
		sessionDir = os.path.join(paths.SESSION_DIR, sessDirRel)

		# Keep track of whether we
		madeAnyFiles = False

		# Convert each flv clip to mp4 & get durations
		for (iVid, vid) in enumerate(vidNames):
			vidPath = os.path.join(paths.VIDEO_DIR, vid)

			# Only process videos in whichFrames if argument given
			if len(whichFrames):
				if not any([fr in vid for fr in whichFrames]):
					continue

			# If not replacing: check that we haven't already (tried to) make this mp4
			mergedFilename = vid[:-4] + '_' + suffix + '.mp4'
			mergedPath = os.path.join(sessionDir, mergedFilename)

			if not replace and os.path.exists(mergedPath) and vid in cls.videoData.keys() and \
				('mp4Dur_' + suffix) in cls.videoData[vid].keys() and ('mp4Path_' + suffix) in cls.videoData[vid].keys() and \
				cls.videoData[vid]['mp4Path_' + suffix]:
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
			filterComplexVideo = "[0:v]drawtext='fontfile=/Library/Fonts/Arial Black.ttf':text='"+frameId + '_' + '_' + sessStr + '_' + timestamp + "':fontsize=16:fontcolor=red:x=10:y=10,setpts=PTS-STARTPTS" + trimStrVideo + "[v0]"
			noAudioPath = os.path.join(sessionDir, vid[:-4] + '_video.mp4')
			sp.call([paths.FFMPEG, '-i', vidPath, '-filter_complex',
	filterComplexVideo, '-map', '[v0]', '-c:v', 'libx264', '-an', '-vsync', 'cfr', '-r', '30', '-crf', '18', noAudioPath, '-loglevel', cls.loglevel])
			madeAnyFiles = True

			# Check that the last N seconds contain video
			videoOnlyDur = videoutils.get_video_details(noAudioPath, ['duration'], fullpath=True)

			if videoOnlyDur > 0:
				if display:
					print "Making {} mp4 for vid: {}".format(suffix, vid)

				# Make audio-only file
				filterComplexAudio = '[0:a]' + trimStrAudio + 'asetpts=PTS-STARTPTS,apad=pad_len=100000'
				audioPath = os.path.join(sessionDir, vid[:-4] + '_audio.m4a')
				sp.call([paths.FFMPEG, '-i', vidPath, '-vn', '-filter_complex', filterComplexAudio, '-c:a', 'libfdk_aac', '-loglevel', cls.loglevel, audioPath])

				audioOnlyDur = videoutils.get_video_details(audioPath, ['duration'], fullpath=True)
				# If we don't have audio, just use use the video file
				if audioOnlyDur in [0, -1]:
					sp.call(['mv', noAudioPath, mergedPath])
				else: # Otherwise, put audio and video together
					sp.call([paths.FFMPEG, '-i', noAudioPath,  '-i', audioPath, '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-loglevel', cls.loglevel, mergedPath])

				# Check the duration of the newly created clip
				(dur, startTime) = videoutils.get_video_details(mergedPath, ['duration', 'starttime'],	fullpath=True)

				# Save the (relative) path to the mp4 and its duration
				vidData[vid] = {}
				vidData[vid]['mp4Dur' + '_' + suffix] = dur
				vidData[vid]['mp4Path' + '_' + suffix] = os.path.join(sessDirRel, mergedFilename)


		# Clean up intermediate audio/video-only files
		if madeAnyFiles:
			sp.call('rm ' + os.path.join(sessionDir, '*_video.mp4'), shell=True)
			sp.call('rm ' + os.path.join(sessionDir, '*_audio.m4a'), shell=True)

		return vidData

	@classmethod
	def concat_mp4s(cls, concatPath, vidPaths):
		'''Concatenate a list of mp4s into a single new mp4.

		concatPath: full path to the desired new mp4 file, including
			extension vidPaths: relative paths (within paths.SESSION_DIR) to
			the videos to concatenate. Videos will be concatenated in the
			order they appear in this list.

		Return value: vidDur, the duration of the video stream of the
			concatenated mp4 in seconds. vidDur is 0 if vidPaths is empty,
			and no mp4 is created.'''

		concat = [paths.FFMPEG]
		inputList = ''

		# If there are no files to concat, immediately return 0.
		if not len(vidPaths):
			return 0

		# Check whether we have audio for each component file
		hasAudio = [(not videoutils.get_video_details(vid, ['audduration'], fullpath=True) == 0) for vid in vidPaths]

		# Build the concatenate command
		for (iVid, vid) in enumerate(vidPaths):
			concat = concat + ['-i', os.path.join(paths.SESSION_DIR, vid)]
			if all(hasAudio):
				inputList = inputList + '[{}:0][{}:1]'.format(iVid, iVid)
			else:
				inputList = inputList + '[{}:0]'.format(iVid)

		# Concatenate the videos
		concat = concat + ['-filter_complex', inputList + 'concat=n={}:v=1:a={}'.format(len(vidPaths), 1*(all(hasAudio))) + '[out]',
			'-map', '[out]', concatPath, '-loglevel', 'error', "-c:v", "libx264", "-preset", "slow",
			"-b:v", "1000k", "-maxrate", "1000k", "-bufsize", "2000k",
			"-c:a", "libfdk_aac", "-b:a", "128k"]

		sp.call(concat)

		# Check and return the duration of the video stream
		vidDur = videoutils.get_video_details(concatPath, 'vidduration', fullpath=True)
		return vidDur

	@classmethod
	def batch_id_for_filename(cls, expId, batchFilename):
		'''Returns the batch ID for a given experiment & batch filename.'''

		batches = load_batch_data(expId)
		if not len(batchFilename):
			raise ValueError('remove_batch: must provide either batchId or batchFilename')
		for id in batches.keys():
			if batches[id]['batchFile'] == batchFilename:
				return id
		raise ValueError('remove_batch: no batch found for filename {}'.format(batchFilename))

	@classmethod
	def export_accounts(cls):
		'''Create a .csv sheet showing all account data.

		All fields except password and profiles will be included. Instead of the list of child
		profile dicts under 'profiles', the individual dicts will be expanded as
		child[N].[fieldname] with N starting at 0.
		'''
		cls.load_account_data() # since this may be called without initializing an instance

		accs = []
		headers = set()
		allheaders = set()
		for (userid, acc) in cls.accounts.items():
			thisAcc = acc['attributes']
			thisAcc['username'] = userid
			profiles = thisAcc['profiles']
			del thisAcc['profiles']
			del thisAcc['password']
			headers = headers | set(thisAcc.keys())
			iCh = 0
			if profiles:
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


	def __init__(self, expId, trimLength=None):
		self.expId = expId
		self.batchData = self.load_batch_data(expId)
		self.coding = self.load_coding(expId)
		self.sessions = self.load_session_data(expId)
		self.videoData = self.load_video_data()
		self.accounts = self.load_account_data()
		self.email = self.load_email_data(expId)
		self.trimLength = trimLength
		print 'initialized study {}'.format(expId)

	def update_session_data(self):
		'''Pull updated session data from server, save, and load into this experiment.'''
		update_session_data(self.expId, display=False)
		self.sessions = self.load_session_data(self.expId)

	def update_video_data(self, newVideos=[], reprocess=False, resetPaths=False,
		display=False):
		'''Updates video data file for this experiment.

		keyword args:

		newVideos: If [] (default), process all video
			names in the video directory that are not already in the video
			data file. Otherwise process only the list newVideos. Should be
			a list of filenames to find in VIDEO_DIR. If 'all', process all
			video names in the video directory.

		reprocess: Whether to
			reprocess filenames that are already in the data file. If true,
			recompute framerate/duration (BUT DO NOT CLEAR BATCH DATA).
			Default false (skip filenames already there). Irrelevant if
			newVideos==[].

		resetPaths: Whether to reset mp4Path/mp4Dur
			fields (e.g. mp4Path_whole, mp4Path_trimmed) to ''/-1 (default
			False)

		Returns: (sessionsAffected, improperFilenames, unmatchedVideos)

		sessionsAffected: list of sessionIds (as for indexing into
			coding)

		improperFilenames: list of filenames skipped because
			they couldn't be parsed

		unmatchedFilenames: list of filenames
			skipped because they couldn't be matched to any session data

		'''

		# Get current list of videos
		videoFilenames = paths.get_videolist()

		# Parse newVideos input
		if len(newVideos) == 0:
			newVideos = list(set(videoFilenames) - set(self.videoData.keys()))
		elif newVideos=="all":
			newVideos = videoFilenames

		print "Updating video data. Processing {} videos.".format(len(newVideos))

		sessionData = self.sessions['sessions']

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

			# TODO: if it's a consent video, copy it to a separate consent directory
			# (sessions/study/consents/)
			if 'consent' in frameId:
				consentDir = os.path.join(paths.SESSION_DIR, expId, 'consents')
				make_sure_path_exists(consentDir)
				sp.call(['cp', os.path.join(paths.VIDEO_DIR, vidName), os.path.join(consentDir, vidName)])

			# Skip videos for other studies
			if expId != self.expId:
				continue

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
			alreadyHaveRecord = (vidName in self.videoData.keys())
			if (not alreadyHaveRecord) or (reprocess or resetPaths):

				sessionsAffected.append(key) # Keep track of this session

				# Start from either existing record or any default values that need to be added
				if alreadyHaveRecord:
					thisVideo = self.videoData[vidName]
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

				self.videoData[vidName] = thisVideo

		# Save the video data file
		backup_and_save(paths.VIDEO_FILENAME, self.videoData)

		return (sessionsAffected, improperFilenames, unmatchedFilenames)

	def update_videos_found(self):
		'''Use coding & video data to match expected videoname fragments to received videos for this experiment.

		Uses partial filenames in coding[sessKey]['videosExpected'] and searches for
		videos in the videoData that match the expected pattern. The field
		coding[sessKey]['videosFound'] is created or updated to correspond to
		coding[sessKey]['videosExpected']. ...['videosFound'][i] is a list of
		video filenames within VIDEO_DIR that match the pattern in
		...['videosExpected'][i].

		Currently this is very inefficient--rechecks all sessions in the experiment.
		Note that this does not update the actual coding or videoData; these should
		already be up to date.'''

		print "Updating videos found for study {}", self.expId

		# Process each session...
		for sessKey in self.coding.keys():
			# Process the sessKey and check this is the right experiment
			(expIdKey, sessId) = paths.parse_session_key(sessKey)

			# Which videos do we expect? Skip if none.
			shortNames = self.coding[sessKey]['videosExpected']
			self.coding[sessKey]['nVideosExpected'] = len(shortNames)
			if len(shortNames) == 0:
				continue;

			# Which videos match the expected patterns? Keep track & save the list.
			self.coding[sessKey]['videosFound'] = []
			for (iShort, short) in enumerate(shortNames):
				theseVideos = [k for (k,v) in self.videoData.items() if (v['shortname']==short) ]
				if len(theseVideos) == 0:
					warn('update_videos_found: Expected video not found for {}'.format(short))
				self.coding[sessKey]['videosFound'].append(theseVideos)

			self.coding[sessKey]['nVideosFound'] = len([vList for vList in self.coding[sessKey]['videosFound'] if len(vList) > 0])

		# Save coding & video data
		backup_and_save(paths.coding_filename(self.expId), self.coding)

	def make_mp4s_for_study(self, sessionsToProcess='missing', filter={}, display=False,
		trimming=False, suffix='', whichFrames=[]):
		'''Convert flvs to mp4s for sessions in a particular study.

		expId: experiment id, string (ex.: 574db6fa3de08a005bb8f844)

		sessionsToProcess: 'missing', 'all', or a list of session keys (as
			used to index into coding). 'missing' creates mp4s only if they
			don't already exist (both video file and entry in videoData).
			'all' creates mp4s for all session flvs, even if they already
			exist.

		filter: dictionary of codingKey:[value1, value2, ...] pairs that should be required
			in the coding data in
			order for the session to be included in the codesheet. Only sessions
			with a value in the list for this header will be shown. (Most
			common usage is {'consent':['yes']} to only process sessions we have
			already confirmed consent for.) Use 'None' as a value to allow sessions
			where codingKey is not present.

		display: (default False) whether to print out information about
			progress

		trimming: False (default) not to do any trimming of video file, or a
			maximum clip duration in seconds. The last trimming seconds
			(counted from the end of the shortest stream--generally video
			rather than audio) will be kept, or if the video is shorter than
			trimming, the entire video will be kept. As used by make_mp4s.

		suffix: string to append to the mp4 filenames (they'll be named as
			their originating flv filenames, plus "_[suffix]") and to the
			fields 'mp4Path_[suffix]' and 'mp4Dur_[suffix]' in videoData.
			Default ''. As used by make_mp4s.

		whichFrames: list of substrings of video filenames for which we should
			actually do processing, e.g. ['video-consent', 'video-preview'].
			Default of [] means process all frames.

		Calls make_mp4s to actually create the mp4s; see documentation there.

		The following values are set in videoData[video]: 'mp4Dur_[suffix]':
			0 if no video was able to be created, due to missing video or a
			missing video stream. It is also possible for video not to be
			created if there is a video stream, but it stops and then the
			audio stream continues for at least trimming seconds after that.
			'mp4Path_[suffix]': Relative path (from paths.SESSION_DIR) to mp4
			created, or '' if as above mp4 was not created.

		Returns a list of session keys for sessions where any video was created.'''

		print "Making {} mp4s for study {}".format(suffix, self.expId)

		if sessionsToProcess in ['missing', 'all']:
			sessionKeys = self.coding.keys()
		else:
			# Make sure list of sessions is unique
			sessionKeys = list(set(sessionsToProcess))

		# Only process data that passes filter
		for (key, vals) in filter.items():
			sessionKeys = [sKey for sKey in sessionKeys if (key in self.coding[sKey].keys() and self.coding[sKey][key] in vals) or
				(key not in self.coding[sKey].keys() and None in vals)]

		sessionsAffected = []

		# Process each session...
		for sessKey in sessionKeys:
			# Process the sessKey and check this is the right experiment
			(expIdKey, sessId) = paths.parse_session_key(sessKey)
			if not expIdKey == self.expId:
				print "Skipping session not for this ID: {}".format(sessKey)
				continue

			# Which videos do we expect? Skip if none.
			shortNames = self.coding[sessKey]['videosExpected']
			if len(shortNames) == 0:
				continue;

			# Expand the list of videos we'll need to process
			vidNames = []
			for vids in self.coding[sessKey]['videosFound']:
				vidNames = vidNames + vids

			# Choose a location for the concatenated videos
			sessDirRel = os.path.join(self.expId, sessId)
			sessionDir = os.path.join(paths.SESSION_DIR, sessDirRel)
			make_sure_path_exists(sessionDir)

			# Convert each flv clip to mp4 & get durations

			if display:
				print 'Session: ', sessId

			replace = sessionsToProcess == 'all'

			mp4Data = self.make_mp4s(sessDirRel, vidNames, display, trimming=trimming,
				suffix=suffix, replace=replace, whichFrames=whichFrames)

			for vid in mp4Data.keys():
				# Save the (relative) path to the mp4 and its duration in video data
				# so we can use it when concatenating these same videos into another
				# file
				self.videoData[vid]['mp4Path' + '_' + suffix] = mp4Data[vid]['mp4Path' + '_' + suffix]
				self.videoData[vid]['mp4Dur' + '_' + suffix] = mp4Data[vid]['mp4Dur' + '_' + suffix]

			if any([not mp4Data[vid]['mp4Dur' + '_' + suffix] == 0 for vid in mp4Data.keys()]):
				sessionsAffected.append(sessKey)


		# Save coding & video data
		backup_and_save(paths.VIDEO_FILENAME, self.videoData)

		return sessionsAffected

	def concatenate_session_videos(self, sessionKeys, filter={}, replace=False, display=False):
		'''Concatenate videos within the same session for the specified sessions.

		Should be run after update_videos_found as it relies on videosFound
			in coding. Does create any missing _whole mp4s but does not
			replace existing ones.

		expId: experiment ID to concatenate videos for. Any sessions
			associated with other experiments will be ignored (warning
			shown).

		sessionKeys: 'all', 'missing', or a list of session keys
			to process, e.g. as returned by update_video_data. Session keys
			are the IDs in session data and the keys for the coding data.

		filter: dictionary of codingKey:[value1, value2, ...] pairs that should be required
			in the coding data in
			order for the session to be included in the codesheet. Only sessions
			with a value in the list for this header will be shown. (Most
			common usage is {'consent':['yes']} to only process sessions we have
			already confirmed consent for.) Use 'None' as a value to allow sessions
			where codingKey is not present.

		replace: whether to replace existing concatenated files (default
			False)

		display: whether to show debugging output (default False)

		For each session, this: - uses videosFound in the coding file to
			locate (after creating if necessary) single-clip mp4s
			with text labels - creates a concatenated mp4 with all video for
			this session (in order) in SESSION_DIR/expId/sessId/, called
			expId_sessId.mp4

		Saves expectedDuration and actualDuration to coding data. '''

		print "Making concatenated session videos for study {}".format(self.expId)

		useTrimmedFrames = ['pref-phys-videos'] # TODOGEOM
		useWholeVideoFrames = ['video-preview', 'video-consent']
		skipFrames = ['video-consent']

		if sessionKeys in ['missing', 'all']:
			sessionKeys = self.coding.keys()
		else:
			# Make sure list of sessions is unique
			sessionKeys = list(set(sessionKeys))

		# Only process data that passes filter
		for (key, vals) in filter.items():
		   sessionKeys = [sKey for sKey in sessionKeys if (key in self.coding[sKey].keys() and self.coding[sKey][key] in vals) or
			   (key not in self.coding[sKey].keys() and None in vals)]

		sessionsAffected = self.make_mp4s_for_study(sessionsToProcess=sessionKeys, display=display,
			trimming=self.trimLength, suffix='trimmed', whichFrames=useTrimmedFrames)

		sessionsAffected = sessionsAffected + self.make_mp4s_for_study(sessionsToProcess=sessionKeys, display=display,
			trimming=False, suffix='whole', whichFrames=useWholeVideoFrames)

		# Process each session...
		for sessKey in sessionKeys:

			# Process the sessKey and check this is the right experiment
			(expIdKey, sessId) = paths.parse_session_key(sessKey)
			if not expIdKey == self.expId:
				print "Skipping session not for this ID: {}".format(sessKey)
				continue

			if display:
				print 'Session: ', sessKey

			# Choose a location for the concatenated videos
			sessDirRel = os.path.join(self.expId, sessId)
			sessionDir = os.path.join(paths.SESSION_DIR, sessDirRel)
			make_sure_path_exists(sessionDir)
			concatFilename = self.expId + '_' +	 sessId + '.mp4'
			concatPath = os.path.join(sessionDir, concatFilename)

			# Skip if not replacing & file exists & we haven't made any new mp4s for this session
			if not replace and os.path.exists(concatPath) and sessKey not in sessionsAffected:
				print "Skipping, already have concat file: {}".format(concatFilename)
				continue

			# Which videos match the expected patterns? Keep track of inds, timestamps, names.
			vidNames = []
			vidInds = []
			for (i, vids) in enumerate(self.coding[sessKey]['videosFound']):
				vidNames = vidNames + vids
				vidInds	 = vidInds + [i] * len(vids)
			vidTimestamps = [(paths.parse_videoname(v)[3], v) for v in vidNames]
			# whether we should use the 'whole' mp4
			useWhole = [any([fr in vid for fr in useWholeVideoFrames]) for vid in vidNames]

			vidData = zip(vidNames, vidInds, vidTimestamps, useWhole)

			# Remove vidNames we don't want in the concat file
			for skip in skipFrames:
				vidData = [vid for vid in vidData if skip not in vid[0]]

			# Also skip any other frames where video was ended early
			# TODOGEOM
			vidData = [vid for vid in vidData if not self.coding[sessKey]['endedEarly'][vid[1]]]

			# Sort the vidData found by timestamp so we concat in order.
			vidData = sorted(vidData, key=lambda x: x[2])

			# Check we have the duration stored (proxy for whether video conversion worked/have any video)
			vidData = [vid for vid in vidData if  (not vid[3] and len(self.videoData[vid[0]]['mp4Path_trimmed'])) or \
													  (vid[3] and len(self.videoData[vid[0]]['mp4Path_whole']))]


			if len(vidData) == 0:
				warn('No video data for session {}'.format(sessKey))
				continue

			expDur = 0
			concatDurations = [self.videoData[vid[0]]['mp4Dur_whole'] if vid[3] else self.videoData[vid[0]]['mp4Dur_trimmed'] for vid in vidData]
			expDur = sum(concatDurations)

			# Concatenate mp4 videos

			concatVids = [os.path.join(paths.SESSION_DIR, self.videoData[vid[0]]['mp4Path_whole']) if \
					vid[3] else os.path.join(paths.SESSION_DIR, self.videoData[vid[0]]['mp4Path_trimmed']) \
					for vid in vidData]
			vidDur = self.concat_mp4s(concatPath, concatVids)

			if display:
				print 'Total duration: expected {}, actual {}'.format(expDur, vidDur)
				# Note: "actual total dur" is video duration only, not audio or standard
				# "overall" duration. This is fine for our purposes so far where we don't
				# need exactly synchronized audio and video in the concatenated files
				# (i.e. it's possible that audio from one file might appear to occur during
				# a different file (up to about 10ms per concatenated file), but would
				# need to be fixed for other purposes!

			# Warn if we're too far off (more than one video frame at 30fps) on
			# the total duration
			if abs(expDur - vidDur) > 1./30:
				warn('Predicted {}, actual {}'.format(expDur, vidDur))

			vidsShown = [self.coding[sessKey]['videosShown'][vid[1]] for vid in vidData]

			 # TODOGEOM
			self.coding[sessKey]['concatShowedAlternate'] = [self.coding[sessKey]['showedAlternate'][i] for (vidName, i, t, useW) in vidData]
			self.coding[sessKey]['concatVideosShown'] = vidsShown

			self.coding[sessKey]['expectedDuration'] = expDur
			self.coding[sessKey]['actualDuration']	 = vidDur
			self.coding[sessKey]['concatVideos'] = concatVids
			self.coding[sessKey]['concatDurations'] = concatDurations

		backup_and_save(paths.coding_filename(self.expId), self.coding)

	def sync_coding_data(self, codeDataName):
		'''Hopefully one-time script to update coding data when replacing concatenated
		files by those made on a different computer - specific to physics study'''

		otherCodingFile = os.path.join(paths.DATA_DIR, codeDataName)

		if os.path.exists(otherCodingFile):
			with open(otherCodingFile,'rb') as f:
				otherCoding = pickle.load(f)

		replaceFields = ['concatShowedAlternate', 'concatVideosShown', 'expectedDuration',
			'actualDuration', 'concatVideos', 'concatDurations']

		for sessKey in self.coding.keys():
			for field in replaceFields:
				print field
				if sessKey in otherCoding.keys() and field in otherCoding[sessKey].keys():
					print otherCoding[sessKey][field]
					self.coding[sessKey][field] = otherCoding[sessKey][field]
				else:
					print "skipping"

		backup_and_save(paths.coding_filename(self.expId), self.coding)

	def batch_videos(self, batchLengthMinutes=5, codingCriteria={'consent':['yes'], 'usable':['yes']},
		includeIncompleteBatches=True):
		''' Create video batches for a study.

		expId: experiment id, string (ex.: 574db6fa3de08a005bb8f844)

		batchLengthMinutes: minimum batch length in minutes. Videos will be
			added to one batch until they exceed this length.

		codingCriteria: a dictionary of requirements on associated coding
			data for videos to be included in a batch. keys are keys within a
			coding record (e.g. 'consent') and values are lists of acceptable
			values. Default {'consent':['yes'], 'usable':['yes']}. Values are
			insensitive to case and leading/trailing whitespace.

		includeIncompleteBatches: whether to create a batch for the
			"leftover" files even though they haven't gotten to
			batchLengthMinutes long yet.

		Trimmed mp4s (ending in _trimmed.mp4) are used for the batches. These
			must already exist--call make_mp4s_for_study first. Only videos
			not currently in any batch will be added to a batch.

		Batch mp4s are named [expId]_[short random code].mp4 and are stored
			in paths.BATCH_DIR. Information about the newly created batches
			is stored in two places: - batch data: adds new mapping batchKey
			: {'batchFile': batchFilename, 'videos': [(sessionKey, flvName,
			duration), ...] } - videoData: add
			videoData[flvName]['inBatches'][batchId] = index in batch

		'''

		print "Making video batches for study {}".format(self.expId)

		vidsToProcess = []

		# First, find all trimmed, not-currently-in-batches videos for this study.
		for sessKey in self.coding.keys():
			for vidList in self.coding[sessKey]['videosFound']:
				for vid in vidList:
					if 'mp4Path_trimmed' in self.videoData[vid].keys():
						mp4Path = self.videoData[vid]['mp4Path_trimmed']
						mp4Dur	= self.videoData[vid]['mp4Dur_trimmed']
						if len(mp4Path) and mp4Dur and not len(self.videoData[vid]['inBatches']):
							vidsToProcess.append((sessKey, vid))

		# Check for coding criteria (e.g. consent, usable)
		for (criterion, values) in codingCriteria.items():
			values = [v.lower().strip() for v in values]
			vidsToProcess = [(sessKey, vid) for (sessKey, vid) in vidsToProcess if self.coding[sessKey][criterion].lower().strip() in values]

		# Separate list into batches; break off a batch whenever length exceeds
		# batchLengthMinutes
		batches = []
		batchDurations = []
		currentBatch = []
		currentBatchLen = 0
		for (iVid, (sessKey, vid)) in enumerate(vidsToProcess):
			dur = self.videoData[vid]['mp4Dur_trimmed']
			currentBatch.append((sessKey, vid, dur))
			currentBatchLen += dur

			# Check if size of videos changes between this & next video
			sizeMismatch = False
			if (iVid + 1) < len(vidsToProcess):
				currentBatchWidth = videoutils.get_video_details(vid, 'width')
				nextBatchWidth = videoutils.get_video_details(vidsToProcess[iVid+1][1], 'width')
				sizeMismatch = nextBatchWidth != currentBatchWidth

			if sizeMismatch or (currentBatchLen > batchLengthMinutes * 60):
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
				concatFilename = self.expId + '_' + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5)) + '.mp4'
				done = concatFilename not in paths.get_batchfiles()
			concatPath = os.path.join(paths.BATCH_DIR, concatFilename)
			print concatPath

			# Get full paths to videos
			batchPaths = [os.path.join(paths.SESSION_DIR, self.videoData[vid]['mp4Path_trimmed']) for (sessKey, vid, dur) in batchList]

			# Create the batch file
			batchDur = self.concat_mp4s(concatPath, batchPaths)

			print "Batch duration -- actual: {}, expected: {}".format(batchDur, batchDurations[iBatch])
			durDiff = batchDur - batchDurations[iBatch]
			if durDiff > 0.033: # Greater than one frame at 30fps
				warn('Difference between predicted and actual batch length, batch filename {}'.format(concatFilename))

			# Add the batch to the videoData file
			self.add_batch(concatFilename, batchList)

	def add_batch(self, batchFilename, videos):
		'''Add a batched video to data files.

		expId: experiment id, string (ex.: 574db6fa3de08a005bb8f844)
			batchFilename: filename of batch video file within batch dir (not
			full path)

		videos: ordered list of (sessionId, videoFilename,
			duration) tuples. sessionId is an index into the coding
			directory, videoFilename is the individual filename (not full
			path).

		The batch data file for this experiment will be updated to include
			this batch (see bat definition) and the videoData for all
			included videos will be updated with their positions within this
			batch: videoData[videoname]['inBatches'][batId] = iVid (index in
			this batch) '''

		batchDur = videoutils.get_video_details(os.path.join(paths.BATCH_DIR, batchFilename),
			 'vidduration', fullpath=True)

		# Create a batch dict for this batch
		bat = { 'batchFile': batchFilename,
				'videos': videos,
				'duration': batchDur,
				'expected': sum([v[2] for v in videos]),
				'addedOn': '{:%Y-%m-%d%H:%M:%S}'.format(datetime.datetime.now()),
				'codedBy': [] }

		# Add this batch to the existing batches
		batId = uuid.uuid4().hex
		self.batchData[batId] = bat

		# Add references to this batch in each videoData record affected
		for (iVid, (sessionId, videoname, dur)) in enumerate(videos):
			self.videoData[videoname]['inBatches'][batId] = iVid

		# Save batch and video data
		backup_and_save(paths.batch_filename(self.expId), self.batchData)
		backup_and_save(paths.VIDEO_FILENAME, self.videoData)

	def remove_batch(self, batchId='', batchFilename='', deleteVideos=False):
		'''Remove a batched video from the data files (batch and video data).

		Either batchId or batchFilename must be provided. batchId is the ID
			used as a key in the batch data file for this experiment;
			batchFilename is the filename within the batch directory. If both
			are provided, only batchId is used.

		If batchId is 'all', all batches for this study are removed from the
			batch and video data files.

		deleteVideos (default false): whether to remove the specified batch
			videos in the batch dir as well as records of them

		Batch data will be removed from the batch file for this experiment
			and from each included video in videoData.'''

		# First handle special case of removing all batches for this experiment
		if batchId == 'all':
			# Remove references to batches in all videoData for this study
			for (vid, vidData) in self.videoData.items():
				vidExpId = paths.parse_videoname(vid)[0]
				if vidExpId == self.expId:
					self.videoData[vid]['inBatches'] = {}
			backup_and_save(paths.VIDEO_FILENAME, self.videoData)
			# Empty batch data file
			backup_and_save(paths.batch_filename(self.expId), {})
			# Remove batch videos
			if deleteVideos:
				for batchVideoname in paths.get_batchfiles():
					vidExpId = batchVideoname.split('_')[0]
					if vidExpId == self.expId:
						sp.call('rm ' + os.path.join(paths.BATCH_DIR, batchVideoname), shell=True)

			return

		# Use filename if provided instead of batchId
		if not batchId:
			batchId = self.batch_id_for_filename(self.expId, batchFilename)

		# Remove this batch from batch data
		videos = self.batchData[batchId]['videos']
		vidName = self.batchData[batchId]['batchFile']
		del self.batchData[batchId]

		# Remove references to this batch in each videoData record affected
		for (iVid, (sessionId, videoname, dur)) in enumerate(videos):
			del self.videoData[videoname]['inBatches'][batchId]

		# Backup and save batch and video data
		backup_and_save(paths.batch_filename(expId), self.batchData)
		backup_and_save(paths.VIDEO_FILENAME, self.videoData)
		print 'Removed batch from batch and video data'

		# Delete video
		if deleteVideos:
			batchPath = os.path.join(paths.BATCH_DIR, vidName)
			if os.path.exists(batchPath):
				sp.call('rm ' + batchPath, shell=True)
				print 'Deleted batch video'

	def empty_coding_record(self):
		'''Return a new instance of an empty coding dict'''
		emptyRecord = {'consent': 'orig',
				'consentnotes': '',
				'usable': '',
				'withdrawn': None,
				'feedback': '',
				'ageRegistration': -1,
				'ageExitsurvey': -1,
				'videosExpected': [],
				'videosFound': [],
				'allcoders': [],
				'expectedDuration': None,
				'actualDuration': None,
				'concatDurations': [],
				'concatVideos': []}
		for field in self.coderFields:
			emptyRecord[field] = {} # CoderName: 'comment'
		return emptyRecord

	def update_coding(self, display=False):
		'''Update coding data with empty records for any new sessions in saved session
		data, which video files are expected, withdrawn status, & birthdates.'''

		updated = False

		# If any existing coding records are missing expected fields, add them
		for (sessId, code) in self.coding.iteritems():
			empty = self.empty_coding_record()
			for missingKey in set(empty.keys()) - set(code.keys()):
				code[missingKey] = empty[missingKey]
				updated = True

		# Create empty coding records for all the new session IDs & update coding dict
		sessIds = [self.sessions['sessions'][iSess]['id'] for iSess in \
						range(len(self.sessions['sessions']))]
		newIds = list(set(sessIds) - set(self.coding.keys()))
		newCoding = dict((k, self.empty_coding_record()) for k in newIds)

		self.coding.update(newCoding)

		# For all sessions, update some critical information - videos expected,
		# withdrawn status, age

		for iSess in range(len(self.sessions['sessions'])):
			sessId = self.sessions['sessions'][iSess]['id']
			expData = self.sessions['sessions'][iSess]['attributes']['expData']

			# Get list of video files expected
			self.coding[sessId]['videosExpected'] = []
			self.coding[sessId]['showedAlternate'] = []
			self.coding[sessId]['endedEarly'] = []
			self.coding[sessId]['videosShown'] = []
			for (frameId, frameData) in expData.iteritems():
				# TODO: generalize for other frames, event names
				# TODOGEOM
				if 'videoId' in frameData.keys() and not frameId=='32-32-pref-phys-videos':
					if 'pref-phys-videos' in frameId:

						# Check events: was the video paused?
						events = [e['eventType'] for e in frameData['eventTimings']]
						showAlternate = 'exp-physics:startAlternateVideo' in events

						# Was the alternate video also paused, if applicable?
						# TODO: once we have an F1 event, add this as a way the study could be ended early
						# Ended early if we never saw either test or alternate video (check
						# for alternate b/c of rare case where due to lots of pausing only
						# alternate is shown)
						endedEarly = 'exp-physics:startTestVideo' not in events and 'exp-physics:startAlternateVideo' not in events
						# Check that the alternate video wasn't paused
						if showAlternate:
							lastAlternateEvent = len(events) - events[::-1].index('exp-physics:startAlternateVideo') - 1
							endedEarly = endedEarly or ('exp-physics:pauseVideo' in events[lastAlternateEvent:])
						# Check we didn't pause test video, but never get to alternate (e.g. F1)
						if not endedEarly and 'exp-physics:pauseVideo' in events and 'exp-physics:startTestVideo' in events:
							lastPause = len(events) - events[::-1].index('exp-physics:pauseVideo') - 1
							firstTest = events.index('exp-physics:startTestVideo')
							endedEarly = endedEarly or (lastPause > firstTest and not showAlternate)

						# Which video file was actually shown?
						thisVideo = ''
						if 'videosShown' in frameData.keys() and len(frameData['videosShown']):
							videos = frameData['videosShown']
							thisVideo = os.path.splitext(os.path.split(videos[0 + showAlternate])[1])[0]

					else:
						showAlternate = None
						thisVideo = None
						endedEarly = None

					self.coding[sessId]['videosExpected'].append(frameData['videoId'])
					self.coding[sessId]['showedAlternate'].append(showAlternate)
					self.coding[sessId]['videosShown'].append(thisVideo)
					self.coding[sessId]['endedEarly'].append(endedEarly)

			withdrawSegment = 'exit-survey'
			exitbirthdate = []
			for (k,v) in expData.items():
				if k[-len(withdrawSegment):] == withdrawSegment:
					if 'withdrawal' in v.keys():
						self.coding[sessId]['withdrawn'] = v['withdrawal']
					if 'birthDate' in v.keys():
						exitbirthdate = v['birthDate']

			session = self.sessions['sessions'][iSess]
			testdate = session['meta']['created-on']

			# Get the (registered) birthdate
			profile = session['attributes']['profileId']
			(username, child) = profile.split('.')
			acc = self.accounts[username]
			childData = [pr for pr in acc['attributes']['profiles'] if pr['profileId']==profile]
			birthdate = childData[0]['birthday']

			testdate = datetime.datetime.strptime(testdate[:10], '%Y-%m-%d')
			birthdate = datetime.datetime.strptime(birthdate[:10], '%Y-%m-%d')
			if exitbirthdate:
				exitbirthdate = datetime.datetime.strptime(exitbirthdate[:10], '%Y-%m-%d')
				self.coding[sessId]['ageExitsurvey'] = float((testdate - exitbirthdate).days) * 12.0/365

			self.coding[sessId]['ageRegistration'] = float((testdate - birthdate).days) * 12.0/365

		backup_and_save(paths.coding_filename(self.expId), self.coding)


		if display:
			printer.pprint(self.coding)

		print "Updated coding with {} new records for experiment: {}".format(len(newCoding), self.expId)

	def generate_batchsheet(self, coderName):
		'''Create a .csv sheet for a coder to mark whether batches are coded.

		coderName: coder in paths.CODERS (e.g. 'Kim') or 'all' to display
			coding status for all coders. Error raised if unknown coder used.

		Fields will be id, minutes (duration of batch in minutes, estimated
			from sum of individual files), batchFile (filename of batch) and
			codedBy-coderName.'''

		if coderName != 'all' and coderName not in paths.CODERS:
			raise ValueError('Unknown coder name', coderName)

		if coderName == 'all':
			coders = paths.CODERS
		else:
			coders = [coderName]

		batchList = []
		for (batchId, bat) in self.batchData.items():

			batchEntry = {	'id': batchId,
							'minutesSum': sum([v[2] for v in bat['videos']])/60,
							'minutesActual': bat.get('duration', -60)/60,
							'addedOn': bat['addedOn'],
							'batchFile': bat['batchFile'],
							'allCoders': ' '.join(bat['codedBy'])}

			for c in coders:
				batchEntry['codedBy-' + c] = 'yes' if c in bat['codedBy'] else 'no'



			batchList.append(batchEntry)

		headers = ['batchFile', 'addedOn', 'id', 'minutesSum', 'minutesActual', 'allCoders']
		for c in coders:
			headers.append('codedBy-' + c)

		for b in batchList:
			for k in b.keys():
				if type(b[k]) is unicode:
					b[k] = b[k].encode('utf-8')

		batchList.sort(key=lambda b: b['addedOn'])

		# Back up any existing batch file by the same name & save
		batchsheetPath = paths.batchsheet_filename(self.expId, coderName)
		backup_and_save_dict(batchsheetPath, batchList, headers)

	def commit_batchsheet(self, coderName):
		'''Update codedBy in the batch file based on a CSV batchsheet.

		Raises IOError if the CSV batchsheet is not found.

		Batch keys are used to match CSV to pickled data records. Only
			whether this coder has completed coding is updated, based on
			the codedBy-[coderName] column. '''

		batchsheetPath = paths.batchsheet_filename(self.expId, coderName)

		field = 'codedBy-' + coderName

		if not os.path.exists(batchsheetPath):
			raise IOError('Batch sheet not found: {}'.format(codesheetPath))

		# Read each row of the coder CSV. 'rU' is important for Mac-formatted CSVs
		# saved in Excel.
		with open(batchsheetPath, 'rU') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				id = row['id']
				if id in self.batchData.keys(): # Match to the actual batch
					if field in row.keys():
						coded = row[field].strip().lower() # Should be 'yes' or 'no'
						if coded == 'yes':
							if coderName not in self.batchData[id]['codedBy']:
								self.batchData[id]['codedBy'].append(coderName)
						elif coded == 'no':
							if coderName in self.batchData[id]['codedBy']:
								self.batchData[id]['codedBy'].remove(coderName)
						else:
							raise ValueError('Unexpected value for whether coding is done for batch {} (should be yes or no): {}'.format(id, coded))
					else:
						warn('Missing expected row header in batch CSV: {}'.format(field))
				else: # Couldn't find this batch ID in the batch dict.
					warn('ID found in batch CSV but not in batch file, ignoring: {}'.format(id))

		# Actually save coding
		backup_and_save(paths.batch_filename(self.expId), self.batchData)

	def generate_codesheet(self, coderName, showOtherCoders=True, showAllHeaders=False,
	includeFields=[], filter={}, ignoreProfiles=[]):
		'''Create a .csv coding sheet for a particular study and coder

		csv will be named expID_coderName.csv and live in the CODING_DIR.

		coderName: name of coder; must be in paths.CODERS. Use 'all' to show
			all coders.

		showOtherCoders: boolean, whether to display columns for other
			coders' coder-specific data

		showAllHeaders: boolean, whether to include all headers or only the
			basics

		includeFields: list of field ENDINGS to include beyond basic headers.
			For each session, any field ENDING in a string in this list will
			be included. The original field name will be removed and the
			corresponding data stored under this partial name, so they should
			be unique endings within sessions. (Using just the ending allows
			for variation in which segment the field is associated with.)

		filter: dictionary of header:[value1, value2, ...] pairs that should be required in
			order for the session to be included in the codesheet. Only records
			with a value in the list for this header will be shown. (Most
			common usage is {'consent':['yes']} to show only records we have
			already confirmed consent for.) This is applied AFTER flattening
			the dict and looking for includeFields above, so it's possible to use
			just the ending of a field if it's also in includeFields. Use 'None' in the
			lists to allow records that don't have this key.

		ignoreProfiles: list of profile IDs not to show, e.g. for test accounts

		'''

		if coderName != 'all' and coderName not in paths.CODERS:
			raise ValueError('Unknown coder name', coderName)

		# Make coding into a list instead of dict
		codingList = []
		headers = set() # Keep track of all headers

		for (key,val) in self.coding.items():
			# Get session information for this coding session
			sess = self.find_session(self.sessions, key)

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
			acc = self.accounts[username]
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

			val['shortId'] = paths.parse_session_key(key)[1]

			# Add any new headers from this session
			headers = headers | set(val.keys())

			codingList.append(val)

		# Organize the headers we actually want to put in the file - headerStart will come
		# first, then alphabetized other headers if we're using them
		headerStart = ['shortId', 'meta.created-on', 'child.profileId', 'consent',
			'withdrawn', 'consentnotes', 'usable', 'feedback',
			'ageRegistration', 'ageExitsurvey', 'allcoders']

		# Insert this and other coders' data here if using
		if coderName == 'all':
			for field in self.coderFields:
				headerStart = headerStart + [h for h in headers if h[:len(field + '.')] == field + '.']
		else:
			headerStart = headerStart + ['coded']
			for field in self.coderFields:
				headerStart = headerStart + [field + '.' + coderName]
				if showOtherCoders:
					headerStart = headerStart + [h for h in headers if h[:len(field + '.')] == field + '.' and h != field + '.' + coderName]

			# Populate the 'coded' field based on allcoders
			for record in codingList:
				record['coded'] = 'yes' if coderName in record['allcoders'] else 'no'

		# Continue predetermined starting list
		# TODOGEOM
		headerStart = headerStart + ['attributes.feedback',
			'attributes.hasReadFeedback', 'attributes.completed', 'nVideosExpected',
			'nVideosFound', 'expectedDuration', 'actualDuration', 'concatVideosShown'] + includeFields + \
			['videosExpected', 'videosFound', 'videosShown', 'showedAlternate', 'endedEarly',
			'child.deleted', 'child.gender', 'child.additionalInformation']

		# Add remaining headers from data if using
		if showAllHeaders:
			headerList = list(headers - set(headerStart))
			headerList.sort()
			headerList = headerStart + headerList
		else:
			headerList = headerStart

		# Filter to show only data that should go in sheet
		for (key, vals) in filter.items():
			codingList = [sess for sess in codingList if (key in sess.keys() and sess[key] in vals) or
				(key not in sess.keys() and None in vals)]

		if ignoreProfiles:
			codingList = [sess for sess in codingList if sess['child.profileId'] not in ignoreProfiles]

		# Reencode anything in unicode
		for record in codingList:
			for k in record.keys():
				if type(record[k]) is unicode:
					record[k] = record[k].encode('utf-8')

		codingList.sort(key=lambda b: b['meta.created-on'])


		# Back up any existing coding file by the same name & save
		codesheetPath = paths.codesheet_filename(self.expId, coderName)
		backup_and_save_dict(codesheetPath, codingList, headerList)

		# Display a quick summary of the data

		#consent / non
		#for each: none, some, all actual study vids
		#for some/all: usability.

		# How many records?
		profileIds = [sess['child.profileId'] for sess in codingList]
		print "Number of records: {} ({} unique)".format(len(codingList), len(list(set(profileIds))))
		hasVideo = [sess['child.profileId'] for sess in codingList if sess['nVideosExpected'] > 0]
		print "Completed consent: {} ({} unique)".format(len(hasVideo),
			len(list(set(hasVideo))))
		for sess in codingList:
			vidsFound = [v for outer in sess['videosFound'] for v in outer]
			sess['nPrefPhys'] = len([1 for v in vidsFound if 'pref-phys-videos' in v])
		consentSess = [sess for sess in codingList if sess['consent'] == 'yes']
		nonconsentSess = [sess for sess in codingList if sess['consent'] != 'yes']

		print "Valid consent: {} ({} unique)".format(
			len(consentSess),
			len(list(set([sess['child.profileId'] for sess in consentSess]))))
		print "\tno physics videos {}, some study videos {}, entire study {} ({} unique)".format(
			len([1 for sess in consentSess if sess['nPrefPhys'] == 0]),
			len([1 for sess in consentSess if 0 < sess['nPrefPhys'] < 24]),
			len([1 for sess in consentSess if sess['nPrefPhys'] >= 24]),
			len(list(set([sess['child.profileId'] for sess in consentSess if sess['nPrefPhys'] >= 24]))))

		print "Invalid consent: {} ({} unique)".format(
			len(nonconsentSess),
			len(list(set([sess['child.profileId'] for sess in nonconsentSess]))))
		print "\tno physics videos {}, some study videos {}, entire study {} ({} unique)".format(
			len([1 for sess in nonconsentSess if sess['nPrefPhys'] == 0]),
			len([1 for sess in nonconsentSess if 0 < sess['nPrefPhys'] < 24]),
			len([1 for sess in nonconsentSess if sess['nPrefPhys'] >= 24]),
			len(list(set([sess['child.profileId'] for sess in nonconsentSess if sess['nPrefPhys'] >= 24]))))

		print "Nonconsent values:"
		display_unique_counts([sess['consent'] for sess in nonconsentSess])
		#printer.pprint([(sess['consent'], sess.get('consentnotes')) for sess in codingList if sess['consent'] not in ['orig', 'yes']])

		print "Usability (for {} valid consent + some video records):".format(len([1 for sess in consentSess if sess['nPrefPhys'] > 0]))
		display_unique_counts([sess['usable'] for sess in consentSess if sess['nPrefPhys'] > 0])

		print "Number of usable sessions per participant:"
		display_unique_counts([sess['child.profileId'] for sess in consentSess if sess['usable']])

		print "Privacy: data from {} consented. \n\twithdrawn {}, private {}, scientific {}, public {}".format(
			len([sess for sess in consentSess if 'exit-survey.withdrawal' in sess.keys()]),
			len([sess for sess in consentSess if sess.get('exit-survey.withdrawal', False)]),
			len([sess for sess in consentSess if not sess.get('exit-survey.withdrawal', False) and sess.get('exit-survey.useOfMedia', False) == 'private']),
			len([sess for sess in consentSess if not sess.get('exit-survey.withdrawal', False) and sess.get('exit-survey.useOfMedia', False) == 'scientific']),
			len([sess for sess in consentSess if not sess.get('exit-survey.withdrawal', False) and sess.get('exit-survey.useOfMedia', False) == 'public']))

		print "Databrary: data from {} consented. \n\tyes {}, no {}".format(
			len([sess for sess in consentSess if 'exit-survey.databraryShare' in sess.keys()]),
			len([sess for sess in consentSess if sess.get('exit-survey.databraryShare', False) == 'yes']),
			len([sess for sess in consentSess if sess.get('exit-survey.databraryShare', False) == 'no']))



	def commit_coding(self, coderName):
		'''Update the coding file for expId based on a CSV edited by a coder.

		Raises IOError if the CSV file is not found.

		Session keys are used to match CSV to pickled data records. Only
			coder fields for this coder (fields in coderFields +
			.[coderName]) are updated.

		Fields are only *added* to coding records if there is a nonempty
			value to place. Fields are *updated* in all cases (even to an
			empty value).'''

		# Fetch coding information: path to CSV, and which coder fields
		codesheetPath = paths.codesheet_filename(self.expId, coderName)
		thisCoderFields = [f + '.' + coderName for f in self.coderFields]

		if not os.path.exists(codesheetPath):
			raise IOError('Coding sheet not found: {}'.format(codesheetPath))

		# Read each row of the coder CSV. 'rU' is important for Mac-formatted CSVs
		# saved in Excel.
		with open(codesheetPath, 'rU') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				id = paths.make_session_key(exp.expId, row['shortId'])
				if id in self.coding.keys(): # Match to a sessionKey in the coding dict.
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
							if genField not in self.coding[id].keys() or coderField not in self.coding[id][genField].keys():
								if len(row[field]):
									print('Adding field {} to session {}: "{}"'.format(field, id, row[field]))
									self.coding[id][genField][coderField] = row[field]

							# Field is already there and this value is new
							elif self.coding[id][genField][coderField] != row[field]:
								print('Updating field {} in session {}: "{}" ->	 "{}"'.format(field, id, self.coding[id][genField][coderField], row[field]))
								self.coding[id][genField][coderField] = row[field]
						else:
							warn('Missing expected row header in coding CSV: {}'.format(field))

					# Separately process coded field and adjust allcoder accordingly
					if 'coded' in row.keys():
						coded = row['coded'].strip().lower() # Should be 'yes' or 'no'
						if coded == 'yes':
							if coderName not in self.coding[id]['allcoders']:
								self.coding[id]['allcoders'].append(coderName)
								print('Marking session {} as coded by {}').format(id, coderName)
						elif coded == 'no':
							if coderName in self.coding[id]['allcoders']:
								self.coding[id]['allcoders'].remove(coderName)
								print('Marking session {} as NOT coded by {}').format(id, coderName)
						else:
							raise ValueError('Unexpected value for whether coding is done for session {} (should be yes or no): {}'.format(id, coded))
					else:
						warn('Missing expected row header "coded" in coding CSV')


				else: # Couldn't find this sessionKey in the coding dict.
					warn('ID found in coding CSV but not in coding file, ignoring: {}'.format(id))

		# Actually save coding
		backup_and_save(paths.coding_filename(self.expId), self.coding)

	def commit_global(self, coderName, commitFields):
		'''Update the coding file for expId based on a CSV edited by a coder;
		edit global fields like consent/usable rather than coder-specific fields.

		expId: experiment id, string
			(ex.: 574db6fa3de08a005bb8f844)

		coderName: name of coder to use CSV file from. Raises IOError if the CSV
			file is not found.

		commitFields: list of headers to commit.

		Session keys are used to match CSV to pickled data records. Fields are
		updated in all cases (even to an empty value).'''

		codesheetPath = paths.codesheet_filename(self.expId, coderName)

		if not os.path.exists(codesheetPath):
			raise IOError('Coding sheet not found: {}'.format(codesheetPath))

		# Read each row of the coder CSV. 'rU' is important for Mac-formatted CSVs
		# saved in Excel.
		with open(codesheetPath, 'rU') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				id = paths.make_session_key(exp.expId, row['shortId'])
				if id in self.coding.keys(): # Match to a sessionKey in the coding dict.
					for field in commitFields:
						if field not in row.keys():
							raise ValueError('Bad commitField name, not found in CSV')

						if field not in self.coding[id].keys():
							print 'Adding field {} to session {}: "{}"'.format(field, id, row[field])
						elif row[field] != self.coding[id][field]:
							print 'Updating field {} for session {}: "{}" to "{}"'.format(field, id, self.coding[id][field], row[field])
						self.coding[id][field] = row[field]

				else: # Couldn't find this sessionKey in the coding dict.
					warn('ID found in coding CSV but not in coding file, ignoring: {}'.format(id))

		# Actually save coding
		backup_and_save(paths.coding_filename(self.expId), self.coding)

	def send_feedback(self):
		'''Send feedback back to JamDB to show to participants from coding data.

		First updates session data from server so we know what feedback is new.

		Does not update feedback based on a coder CSV - need to first run
		commit_global(expId, coderName, ['feedback']) to save feedback to the
		coding file.

		'''

		# Update session data
		update_session_data(self.expId)
		self.sessions = self.load_session_data(self.expId)

		# Set up connection to JamDB
		client = ExperimenterClient(access_token=conf.OSF_ACCESS_TOKEN).authenticate()

		# For each session, look at old and new feedback; update if needed
		for sessKey in self.coding.keys():

			thisSession = self.find_session(self.sessions, sessKey)
			existingFeedback = thisSession['attributes']['feedback']

			newFeedback = self.coding[sessKey]['feedback']

			if newFeedback != existingFeedback:
				print 'Updating feedback for session {}. Existing: {}, new: {}'.format(sessKey, existingFeedback, newFeedback)
				client.set_session_feedback({'id': sessKey}, newFeedback)

		print "Sent updated feedback to server for exp {}".format(self.expId)

	def read_batch_coding(self):
		'''TODO: DOC'''
		for (batchID, batch) in self.batchData.items():
			theseCoders = batch['codedBy']
			printer.pprint([batch['batchFile'], theseCoders])
			# Extract list of lengths to use for demarcating trials
			vidLengths = [v[2] for v in batch['videos']]
			for coderName in theseCoders:
				vcodeFilename = paths.vcode_batchfilename(batch['batchFile'], coderName)
				# Check that the VCode file exists
				if not os.path.isfile(vcodeFilename):
					warn('Expected Vcode file {} for coder {} not found'.format(os.path.basename(vcodeFilename), coderName))
					continue
				# Read in file
				(durations, leftLookTime, rightLookTime, oofTime) = \
					vcode.read_preferential(vcodeFilename, interval=[], videoLengths=vidLengths)
				# Save data
				vcodeData = {'durations': durations, 'leftLookTime': leftLookTime,
					'rightLookTime': rightLookTime, 'oofTime': oofTime}

				if 'vcode' in batch.keys():
					batch['vcode'][coderName] = vcodeData
				else:
					batch['vcode'] = {coderName: vcodeData}
				self.batchData[batchID] = batch

		# Save batch and video data
		backup_and_save(paths.batch_filename(self.expId), self.batchData)

	def read_vcode_coding(self, filter={}):
		'''Check all sessions for this study for expected VCode files & read into coding data.
		TODO: full doc'''

		sessionKeys = filter_keys(self.coding, filter)
		for sessKey in sessionKeys:
			codeRec = self.coding[sessKey]
			theseCoders = codeRec['allcoders']
			vidLengths = codeRec['concatDurations']
			# printer.pprint((sessKey, theseCoders))

			# Extract list of lengths to use for demarcating trials

			for coderName in theseCoders:
				vcodeFilename = paths.vcode_filename(sessKey, coderName, short=True)
				# Check that VCode file exists
				if not os.path.isfile(vcodeFilename):
					warn('Expected Vcode file {} for coder {} not found'.format(os.path.basename(vcodeFilename), coderName))
					continue
				# Read in file
				if coderName == 'Realtime':
					#shift = 500
					shift = 0
				else:
					shift = 0

				(durations, leftLookTime, rightLookTime, oofTime) = \
					vcode.read_preferential(vcodeFilename, interval=[], videoLengths=vidLengths, shift=shift)

				vcodeData = {'durations': durations, 'leftLookTime': leftLookTime,
					'rightLookTime': rightLookTime, 'oofTime': oofTime}

				if 'vcode' in codeRec.keys():
					codeRec['vcode'][coderName] = vcodeData
				else:
					codeRec['vcode'] = {coderName: vcodeData}
				self.coding[sessKey] = codeRec

		# Save batch and video data
		backup_and_save(paths.coding_filename(self.expId), self.coding)

	def summarize_results(self):

		usableSessions = {sKey:c for (sKey, c) in self.coding.items() if c['usable'][:3] == 'yes'}

		nCoded = 0

		plotsToMake = ['prefRight', 'prefOverall', 'prefByConcept', 'controlCorrs', 'calibration', 'totalLT', 'compareCoding']
		#plotsToMake = ['calibration']
		#plotsToMake = ['compareCoding']
		#plotsToMake = ['controlCorrs']
		figNums = {plotName: figNum for (plotName, figNum) in zip(plotsToMake, range(len(plotsToMake)))}

		sessions = []
		calibrationData = []
		calibrationTimes = []
		totalData = []
		stds = []

		stickiness = []
		overallPrefs = []
		salience = []

		diffs = []
		diffStds = []
		allFLTDiffs = []

		useCoder = 'Jessica'

		compCoders = ['Realtime', 'Jessica']

		for (sessKey, codeRec) in usableSessions.items():
			# Check if file is usable. If so, list.
			print (sessKey, codeRec['allcoders'])

			# get child's age
			age = codeRec['ageRegistration']

			if 'compareCoding' in plotsToMake and \
				all([coder in codeRec['allcoders'] for coder in compCoders]):

				vcodedata = codeRec['vcode']

				if all([coder in vcodedata.keys() for coder in compCoders]):
					codingToCompare = [vcodedata[coder] for coder in compCoders]
					lefts = [coding['leftLookTime'] for coding in codingToCompare]
					rights = [coding['rightLookTime'] for coding in codingToCompare]
					flts = [np.divide(lefts[i], lefts[i] + rights[i]) for i in range(len(lefts))]

					leftDiffs = np.abs(np.subtract(lefts[0], lefts[1]))
					rightDiffs = np.abs(np.subtract(rights[0], rights[1]))
					fLTDiffs = np.abs(np.subtract(flts[0], flts[1]))

					meanLTs = 0.5 * (lefts[0] + rights[0] + lefts[1] + rights[1])

					allFLTDiffs = np.concatenate( (allFLTDiffs, [d for (i, d) in enumerate(fLTDiffs) if (not np.isnan(d)) and (meanLTs[i] > 5000)]))

					plt.figure(figNums['compareCoding'])


					plt.subplot(311)
					for i in range(len(flts[0])):
						plt.errorbar(flts[0][i], flts[1][i], fmt='o', markersize=0.001*meanLTs[i])

					diffs.append(np.nanmean(fLTDiffs))
					diffStds.append(np.nanstd(fLTDiffs))


			if useCoder in codeRec['allcoders']: #'Training' not in codeRec['allcoders'] and

				nCoded += 1

				print "{} clips".format(len(codeRec['concatVideos']))
				#printer.pprint(codeRec['concatVideosShown'])
				vcodedata = codeRec['vcode']

				for (coder, coding) in vcodedata.items():
					if coder == useCoder:

						totalLTs = coding['leftLookTime'] + coding['rightLookTime']
						totalData.append([LT for (LT, vidShown) in zip(totalLTs, codeRec['concatVideosShown']) if not vidShown == None])
						preferences = np.divide(coding['leftLookTime'], totalLTs)

						# unexpectedLeft references child's left, preferences are to coder's left = child's right
						prefUnexpected = [1-pref if parse_stimuli_name(stimVid)['unexpectedLeft'] else pref \
							for (pref, stimVid) in zip(preferences, codeRec['concatVideosShown'])]

						parsedVidNames = [parse_stimuli_name(stimVid) for stimVid in codeRec['concatVideosShown']]

						def selectPreferences(prefs, minTrial=0, maxTrial=25, excludeConcepts=[], concepts=[], events=[], requireOneImprob=True):
							thesePrefs = [p for (p, parsed, trialNum) in zip(prefs, parsedVidNames, range(len(prefs))) if \
								((not requireOneImprob) or parsed['unexpectedLeft'] != parsed['unexpectedRight']) and \
								not parsed['concept'] in excludeConcepts and \
								((not concepts) or parsed['concept'] in concepts) and \
								((not events) or parsed['event'] in events) and \
								minTrial <= trialNum <= maxTrial ]
							m = np.nanmean(thesePrefs)
							std = np.nanstd(thesePrefs)
							sem = scipy.stats.sem(thesePrefs, nan_policy='omit')

							return (thesePrefs, m, sem, std)

						(prefUnexpectedOverall, overallMean, overallSem, overallStd) = selectPreferences(prefUnexpected, excludeConcepts=['control'])
						(prefUnexpectedGravity, gravityMean, gravitySem, gravityStd) = selectPreferences(prefUnexpected, concepts=['gravity'])
						(prefUnexpectedSupport, supportMean, supportSem, supportStd) = selectPreferences(prefUnexpected, concepts=['support'], events=['stay'])
						(prefUnexpectedControl, controlMean, controlSem, controlStd) = selectPreferences(prefUnexpected, concepts=['control'])

						if len(prefUnexpectedControl) > 1:
							stds.append(controlStd)
						prefSame = np.abs(np.array(selectPreferences(preferences, events=['same'], requireOneImprob=False)[0]) - 0.5)

						calScores = [vcode.scoreCalibrationTrials(paths.vcode_filename(sessKey, coder, short=True),
															iTrial,
															codeRec['concatDurations'],
															parsed['flip'] == 'LR',
															[-20000, -15000, -10000, -5000]) \
									for (iTrial, parsed) in zip(range(len(parsedVidNames)), parsedVidNames) \
										if parsed['event'] == 'calibration']
						correctTotal = sum([cs[0] for cs in calScores])
						incorrectTotal = sum([cs[1] for cs in calScores])
						calFracs = [float(cs[0])/(cs[0]+cs[1]) if cs[0]+cs[1] else float('nan') for cs in calScores]
						calTimes = [float(cs[0] + cs[1]) if cs[0] + cs[1] else float('nan') for cs in calScores]
						calibrationData.append(calFracs)
						calibrationTimes.append(calTimes)
						sessions.append(sessKey)

						print 'calibration:'
						print calFracs
						#print [parsed in parsedVidNames if parsed['event'] == 'calibration'
						printer.pprint([(parsed['event'], vid) for (parsed, vid) in zip(parsedVidNames, codeRec['concatVideos']) if parsed['event']=='calibration'])

						if correctTotal + incorrectTotal:
							calScoreSummary = float(correctTotal) / (correctTotal + incorrectTotal)
						else:
							calScoreSummary = float('nan')

						if 'prefRight' in plotsToMake:
							plt.figure(figNums['prefRight'])
							plt.plot(preferences, 'o-')

						if 'prefOverall' in plotsToMake:
							plt.figure(figNums['prefOverall'])
							plt.errorbar(age, overallMean, yerr=overallSem, fmt='o', ecolor='g', capthick=2)

						if 'prefByConcept' in plotsToMake:
							plt.figure(figNums['prefByConcept'], figsize=(5,10))
							plt.subplot(411)
							plt.errorbar(age, gravityMean, yerr=gravitySem, fmt='o', ecolor='g', capthick=2)
							plt.subplot(412)
							plt.errorbar(age, supportMean, yerr=supportSem, fmt='o', ecolor='g', capthick=2)
							plt.subplot(413)
							plt.errorbar(age, controlMean, yerr=controlSem, fmt='o', ecolor='g', capthick=2)
							if not np.isnan(calScoreSummary):
								plt.plot([age], [calScoreSummary], 'kx')
							plt.subplot(414)
							plt.plot([age] * len(prefSame), prefSame, 'ro-')

						if 'controlCorrs' in plotsToMake:
							plt.figure(figNums['controlCorrs'], figsize=(4,8))
							plt.subplot(211)
							stickiness.append(np.nanmean(prefSame))
							overallPrefs.append(overallMean)
							salience.append(controlMean)

							plt.errorbar(np.nanmean(prefSame), overallMean,
								xerr=scipy.stats.sem(prefSame, nan_policy='omit'), yerr=overallSem, fmt='o', capthick=2, ecolor='g')
							plt.subplot(212)
							plt.errorbar(controlMean, overallMean,
								xerr=controlSem, yerr=overallSem, fmt='o', capthick=2, ecolor='g')

			else:
				print '\tNot yet coded'

		print "\n{} records coded".format(nCoded)

		print "stickiness"
		print stickiness
		print "overallPrefs"
		print overallPrefs



		make_sure_path_exists(paths.FIG_DIR)

		agerange = [4, 13]

		if 'compareCoding' in plotsToMake:
			f = plt.figure(figNums['compareCoding'])
			plt.subplot(311)
			plt.title('fLT')
			plt.xlabel(compCoders[0])
			plt.ylabel(compCoders[1])
			plt.subplot(312)
			plt.errorbar(range(len(diffs)), diffs, yerr=diffStds, fmt='o', ecolor='g', capthick=2)
			plt.title('Mean fLT deviation per subject')
			plt.grid(True)
			plt.subplot(313)
			plt.hist(allFLTDiffs, bins=40)
			med = np.median(allFLTDiffs)
			plt.title('Deviation: median {:.2f}, mean {:.2f}'.format(med, np.mean(allFLTDiffs)))
			plt.tight_layout()
			f.savefig(os.path.join(paths.FIG_DIR, 'compCoding.png'))

		if 'totalLT' in plotsToMake:
			f = plt.figure(figNums['totalLT'])
			nTrials = 24
			meanLT = np.divide([np.nanmean([LTs[iT] if (iT < len(LTs)) else float('nan') for LTs in totalData]) for iT in range(nTrials)], 1000)
			semLT = np.divide([scipy.stats.sem([LTs[iT] if (iT < len(LTs)) else float('nan') for LTs in totalData], nan_policy='omit') for iT in range(nTrials)], 1000)
			plt.errorbar(range(nTrials), meanLT, yerr=semLT, fmt='o-', capthick=2)
			plt.xlabel('trial number')
			plt.ylabel('looking time (s)')
			plt.title('Mean total looking time per trial')
			plt.axis([-1,nTrials,0, 20])
			plt.grid(True)
			f.savefig(os.path.join(paths.FIG_DIR, 'totalLT.png'))


		if 'prefRight' in plotsToMake:
			f = plt.figure(figNums['prefRight'])
			plt.axis([0,24,-0.1,1.1])
			plt.ylabel('preference for childs right')
			plt.xlabel('trial number')
			plt.tight_layout()
			f.savefig(os.path.join(paths.FIG_DIR, 'prefRight.png'))

		if 'prefOverall' in plotsToMake:
			f = plt.figure(figNums['prefOverall'])
			plt.axis(agerange + [0.2, 0.8])
			plt.title('Overall preference per child')
			plt.ylabel('preference for unexpected events')
			plt.xlabel('age in months')
			plt.plot(agerange, [0.5, 0.5], 'k-')
			plt.tight_layout()
			f.savefig(os.path.join(paths.FIG_DIR, 'prefOverall.png'))

		if 'prefByConcept' in plotsToMake:
			f = plt.figure(figNums['prefByConcept'])
			plt.subplot(411)
			plt.axis(agerange + [0, 1])
			plt.title('Gravity preference')
			plt.plot(agerange, [0.5, 0.5], 'k-')
			plt.subplot(412)
			plt.axis(agerange + [0, 1])
			plt.title('Support preference')
			plt.plot(agerange, [0.5, 0.5], 'k-')
			plt.subplot(413)
			plt.axis(agerange + [-0.1, 1.1])
			plt.title('Salience preference')
			plt.plot(agerange, [0.5, 0.5], 'k-')
			plt.subplot(414)
			plt.axis(agerange + [-0.05, 0.55])
			plt.title('Stickiness, per trial')
			plt.xlabel('age in months')
			plt.plot(agerange, [0.5, 0.5], 'k-')
			plt.plot(agerange, [0, 0], 'k-')
			plt.tight_layout()
			f.savefig(os.path.join(paths.FIG_DIR, 'prefByConcept.png'))

		if 'controlCorrs' in plotsToMake:

			f = plt.figure(figNums['controlCorrs'])
			plt.subplot(211)
			plt.axis([0, 0.5, 0, 1])
			plt.grid(True)
			(stickR, stickP) =	scipy.stats.spearmanr(stickiness, overallPrefs, nan_policy='omit')
			plt.xlabel('''Stickiness (0 = equal looking,
			0.5 = exclusively one event)''')
			plt.title('r = {:0.2f}, p = {:0.3f}'.format(float(stickR), float(stickP)))
			plt.ylabel('Overall preference unexpected')
			plt.subplot(212)
			plt.axis([0, 1, 0, 1])
			(salR, salP) =	scipy.stats.spearmanr(salience, overallPrefs, nan_policy='omit')
			plt.title('r = {:0.2f}, p = {:0.3f}'.format(float(salR), float(salP)))
			plt.xlabel('Salience preference')
			plt.ylabel('Overall preference unexpected')
			plt.grid(True)
			plt.tight_layout()
			f.savefig(os.path.join(paths.FIG_DIR, 'controlCorrs.png'))

		if 'calibration' in plotsToMake:
			f = plt.figure(figNums['calibration'], figsize=(4,4))
			i = 1
			for (iSubj, (calFracs, s)) in enumerate(zip(calibrationData, sessions)):
				if len(calFracs):
				   plt.plot([i] * len(calFracs), calFracs, 'ko')
				   plt.plot([i-0.1, i+0.1], [np.nanmean(calFracs)] * 2, 'k-')
				   print "{} (...{}): ".format(i, s[-4:]) + str.join(" ", ["%0.2f" % frac for frac in calFracs])

				   i += 1

				#plt.plot(calibrationTimes[iSubj], calFracs, 'o')
			plt.axis([0, i, -0.01, 1.01])
			plt.ylabel('Fraction looking time to correct side')
			plt.xlabel('Participant')
			plt.title('Calibration trials')

			plt.tight_layout()
			f.savefig(os.path.join(paths.FIG_DIR, 'calibration.png'))

		plt.show()



def get_batch_info(expId='', batchId='', batchFilename=''):
		'''Helper: Given either a batchId or batch filename, return batch data for this
		batch. Must supply either expId or batchFilename.

		Returns the dictionary associated with this batch, with field:
			batchFile - filename of batch, within BATCH_DIR videos - list of
			(sessionKey, videoFilename, duration) tuples in order videos
			appear in batch codedBy - list of coders who have coded this
			batch'''

		# Load the batch data for this experiment
		if len(expId):
			batches = load_batch_data(expId)
		elif len('batchFilename'):
			expId = batchFilename.split('_')[0]
			batches = Experiment.load_batch_data(expId)
		else:
			raise ValueError('get_batch_info: must supply either batchFilename or expId')

		# Use filename if provided instead of batchId
		if not len(batchId):
			batchId = Experiment.batch_id_for_filename(expId, batchFilename)

		return batches[batchId]

def filter_keys(sessDict, filter):
	'''Return only session keys from dict that satisfy query given by filter.

	filter is a dictionary of filtKey:[val1, val2, val3, ...] pairs.

	sessDict is a dictionary of sessKey:session pairs.

	The returned keys will contain only sessKey:session pairs for which,
	for all of the pairs in filter, session[filtKey] is in filter[filtKey] OR
	None is in filter[filtKey] and filtKey is not in session.keys().'''

	filteredKeys = sessDict.keys()
	for (key, vals) in filter.items():
		filteredKeys = [sKey for sKey in filteredKeys if (key in sessDict[sKey].keys() and sessDict[sKey][key] in vals) or
			(key not in sessDict[sKey].keys() and None in vals)]
	return filteredKeys

def parse_stimuli_name(stimVid):

	unexpectedOutcomes = {'ramp': ['up'],
						'toss':	 ['up'],
						'table':  ['up', 'continue'],
						'stay': ['near', 'next-to', 'slightly-on'],
						'fall': ['mostly-on'],
						'salience': ['interesting'],
						'same': []}

	if not stimVid:
		concept = None
		unexpectedLeft = False
		unexpectedRight = False
		event = None
		flip = None

	elif 'calibration' in stimVid:
		concept = 'calibration'
		unexpectedLeft = False
		unexpectedRight = False
		event = 'calibration'
		flip = 'RL' if 'RL' in stimVid else 'LR'
	else:
		(_, event, leftOutcome, rightOutcome, object, camera, background, flip) = stimVid.split('_')
		if event in ['ramp', 'toss', 'table']:
			concept = 'gravity'
		elif event in ['stay', 'fall']:
			concept = 'support'
		elif event in ['same', 'salience']:
			concept = 'control'
		else:
			warn('Unrecognized event type')

		unexpectedLeft = leftOutcome in unexpectedOutcomes[event]
		unexpectedRight = rightOutcome in unexpectedOutcomes[event]

	return {'concept': concept, 'unexpectedLeft': unexpectedLeft,
			'unexpectedRight': unexpectedRight, 'event': event,
			'flip': flip}


if __name__ == '__main__':

	helptext = '''
You'll use the program coding.py to create spreadsheets with updated data for you to work
with, and to 'commit' or save the edits you make in those spreadsheets to the underlying
data structures. Note that the spreadsheets you interact with are TEMPORARY files: they
are created, you edit them, and you commit them. Simply saving your spreadsheet from Excel
does NOT commit your work, and it may be overwritten.

In the commands below, YOURNAME is the name we have agreed on for you, generally your
first name with a capital first letter (e.g. 'Audrey'). So if you were told to type
python coding.py --coder YOURNAME
you would actually type
python coding.py --coder Audrey

STUDY is the study name, which can be either the full ID (found in the URL if you find the
correct study on Lookit) or a nickname you'll be told (e.g. 'physics'). Coding/batch sheets
and video data are always stored under the full ID.

To get an updated coding sheet for a particular study:
	python coding.py fetchcodesheet --coder YOURNAME --study STUDY

	This creates a coding spreadsheet named STUDYID_YOURNAME.csv in the coding directory.
	Do not move or rename it. Do not edit the first column, labeled id.

	All other fields are okay to edit/delete/hide,
	but only the ones with a .YOURNAME ending (e.g. coderComments.Audrey) will actually
	be saved when you commit the sheet. Only sessions where consent and usability have
	already been confirmed will be displayed on your sheet. Sessions are sorted by
	date/time.

To commit your coding sheet:
	python coding.py commitcodesheet --coder YOURNAME --study STUDY

	This updates the stored coding data to reflect changes you have made in any fields
	with a .YOURNAME ending in your coder sheet. Your coder sheet must exist and be in the
	expected location/filename for this to work.

To get an updated batch sheet for a particular study:
	python coding.py fetchbatchsheet --coder YOURNAME --study STUDY

	This creates a batch spreadsheet named STUDYID_batches_YOURNAME.csv in the coding
	directory so you can mark which batches you have coded. Each row is a batch; batches
	are sorted by date created. batchFile gives the filename of the batch within the
	batches directory.

	Do NOT edit the 'id' column or move/rename your spreadsheet. When you have coded a
	batch, change the value in the 'codedBy-YOURNAME' field from 'no' to 'yes'.

To commit your batch sheet:
	python coding.py commitbatchsheet --coder YOURNAME --study STUDY

	This updates the stored batch data to reflect changes you have made in the
	codedBy-YOURNAME field of your batch sheet. Your batch sheet must exist and be in the
	expected location/filename for this to work.

----------------- Advanced users & consent coders only -----------------------------------

To do a regular update:
	python coding.py update --study STUDY

	Standard full update. Updates account data, gets new videos, updates sessions, and
	processes video for this study.

To get an updated consent sheet:
	python coding.py fetchconsentsheet --coder YOURNAME --study STUDY

	This works exactly like fetching a coding sheet (and creates the same filename)
	but (a) all sessions (not just those with consent/usability already confirmed) will
	be shown and (b) all fields will be shown.

To commit data from a consent sheet:
	python coding.py commitconsentsheet --coder YOURNAME --study STUDY [--fields a b c ..]

	This commits global (not coder specific) data only from your consent sheet to the
	coding data. Fields committed are 'consent' and 'feedback' unless specified using
	fields (e.g. --fields feedback usable).

To send feedback to users:
	python coding.py sendfeedback --study STUDY

	This sends feedback currently in the coding data to the site, where it will be
	displayed to users. Feedback must first be updated, e.g. using commitconsentsheet.

To view all current coding/batches:
	python coding.py fetchcodesheet --coder all
	python coding.py fetchconsentsheet --coder all
	python coding.py fetchbatchsheet --coder all

	Using --coder all will show coder-specific fields from all coders.

To change the list of coders:
	change in .env file. You won't be able to generate a new coding or batch sheet for
	a coder removed from the list, but existing data won't be affected.

To change what fields coders enter in their coding sheets:
	edit coderFields in Experiment (in coding.py), then update coding.
	(python coding.py updatesessions --study study)

	New fields will be added to coding records the next time coding is
	updated. If an existing codesheet is committed before coding is updated OR a
	new coder sheet is created, a warning will be displayed that an expected field is
	missing.

To create batches of video:
	python coding.py makebatches --study STUDY

	Using any video not already in a batch, forms batches of approximately batchLengthMinutes
	(defined in coding.py) long and adds them to batch data. These will show up on
	batch sheets. Only videos from sessions with usability & consent confirmed are included.

To remove a video batch:
	python coding.py removebatch --study STUDY [--batchID batchID] [--batchFile batchFile]

	Remove the .mp4 and the record of a particular batch. Must provide either batch ID
	(from a batch sheet) or filename within the batch directory. Use --batchID all to
	remove all batches from a given study.

To check for missing video:
	Look at a coding sheet -- can see nVideosExpected and nVideosFound fields.

To check for issues with batch concatenation, where total file length != sum of individual
	file lengths:
	Look at a batch sheet -- compare minutesSum (sum of individual file lengths) and
	minutesActual (duration of video stream of batch mp4).

To look for and process VCode files for batch videos:
	python coding.py updatevcode --study STUDY

To use the staging database:
	add the argument --config .env-staging to any other command

If videos had to be created on a different computer:
	move videodata file to TMI
	move videos to TMI
	move coding data file to TMI under new name in data dir
	run exp.sync_coding_data(newCodingFileName)

Partial updates:

	To get updated account data:
		python coding.py updateaccounts

		This gets updated account information from the server and creates a file
		accounts.csv in the coding directory. It is recommended to update account data *before*
		updating study data since new accounts may have participated.

	To get updated videos for all studies:
		python coding.py getvideos

		This fetches videos only from the S3 bucket, pulling from wowza to get any very new
		data, and puts them in the video directory directly.

	To get updated session data:
		python coding.py updatesessions --study STUDY

		This fetches session data from the database on the server and updates the coding data
		accordingly.

	To process videos for this study:
		python coding.py processvideo --study STUDY

		This will do some basic video processing on any new videos (not already processed)
		and store the results in the video data file (checking duration & bitrate). It
		checks that there are no video filenames that can't be matched to a session. The coding
		data is updated to show all videos found for each session, matched to the expected videos,
		and videos are converted to mp4 and concatenated by session, with the results stored
		under sessions/STUDYID. (Existing videos are not overwritten.)'''

	ignoreProfiles = ['kim2.smtS6', 'kim2.HVv94', 'bostoncollege.uJG4X', 'sam.pOE5w', 'abought.hqReV']

	standardFields = [	'exit-survey.withdrawal',
						 'exit-survey.useOfMedia',
						 'exit-survey.databraryShare',
						 'exit-survey.feedback',
						 'instructions.confirmationCode',
						 'mood-survey.active',
						 'mood-survey.childHappy',
						 'mood-survey.rested',
						 'mood-survey.healthy',
						 'mood-survey.doingBefore',
						 'mood-survey.lastEat',
						 'mood-survey.napWakeUp',
						 'mood-survey.nextNap',
						 'mood-survey.usualNapSchedule',
						 'mood-survey.ontopofstuff',
						 'mood-survey.parentHappy',
						 'mood-survey.energetic']

	includeFieldsByStudy = {'57a212f23de08a003c10c6cb': [],
							'57adc3373de08a003fb12aad': [],
							'57dae6f73de08a0056fb4165': standardFields,
							'57bc591dc0d9d70055f775db': standardFields,
							'583c892ec0d9d70082123d94': standardFields,
							'58cc039ec0d9d70097f26220': standardFields}

	trimLength = 20
	batchLengthMinutes = 5

	# Fields required for each action
	actions = {'fetchcodesheet': ['coder', 'study'],
			   'commitcodesheet': ['coder', 'study'],
			   'fetchconsentsheet': ['coder', 'study'],
			   'commitconsentsheet': ['coder', 'study'],
			   'sendfeedback': ['study'],
			   'fetchbatchsheet': ['coder', 'study'],
			   'commitbatchsheet': ['coder', 'study'],
			   'updateaccounts': [],
			   'getvideos': [],
			   'updatesessions': ['study'],
			   'processvideo': ['study'],
			   'update': ['study'],
			   'makebatches': ['study'],
			   'removebatch': ['study'],  # must provide batchID or batchFile
			   'exportmat': ['study'],
			   'updatevcode': ['study'],
			   'tests': ['study'],
			   'updatevideodata': ['study']}

	# Parse command-line arguments
	parser = argparse.ArgumentParser(description='Coding operations for Lookit data',
		epilog=helptext, formatter_class=argparse.RawDescriptionHelpFormatter)
	parser.add_argument('action',
		choices=actions.keys(),
		help='Action to take')
	parser.add_argument('--coder', choices=paths.CODERS + ['all'],
		help='Coder name to create sheet or commit coding for')
	parser.add_argument('--study', help='Study ID')
	parser.add_argument('--fields', help='Fields to commit (used for commitconsentsheet only)',
		action='append', default=['consent', 'feedback', 'usable', 'consentnotes'])
	parser.add_argument('--batchID', help='Batch ID to remove, or "all" (used for removebatch only)')
	parser.add_argument('--batchFile', help='Batch filename to remove (used for removebatch only)')
	parser.add_argument('-c', '--config', type=str, default='.env-prod', help='.env file to use; defaults to .env-prod')

	args = parser.parse_args()

	# Additional input-checking for fields required for specific actions
	if 'study' in actions[args.action] and not args.study:
		raise ValueError('Must supply a study ID to use this action.')
	if 'coder' in actions[args.action] and not args.coder:
		raise ValueError('Must supply a coder name to use this action.')

	# Process any study nicknames
	if args.study:
		args.study = paths.studyNicknames.get(args.study, args.study)
		exp = Experiment(args.study, trimLength)
		includeFields = includeFieldsByStudy.get(args.study, [])

	### Process individual actions

	if args.action == 'sendfeedback':
		print 'Sending feedback...'
		exp.send_feedback()

	elif args.action == 'fetchcodesheet':
		print 'Fetching codesheet...'
		exp.generate_codesheet(args.coder, filter={'consent':['yes'], 'exit-survey.withdrawal': [False, None]}, showAllHeaders=False,
			includeFields=includeFields, ignoreProfiles=ignoreProfiles)

	elif args.action == 'fetchconsentsheet':
		print 'Fetching consentsheet...'
		exp.generate_codesheet(args.coder, filter={'nVideosExpected': range(0,100)}, showAllHeaders=True,
			includeFields=includeFields, ignoreProfiles=ignoreProfiles)

		#'consent': ['yes'], 'withdrawn': [False], 'exit-survey.useOfMedia': ['public']

	elif args.action == 'commitcodesheet':
		print 'Committing codesheet...'
		exp.commit_coding(args.coder)

	elif args.action == 'commitconsentsheet':
		print 'Committing consentsheet...'
		exp.commit_global(args.coder, args.fields)

	elif args.action == 'fetchbatchsheet':
		print 'Making batchsheet...'
		exp.generate_batchsheet(args.coder)

	elif args.action == 'commitbatchsheet':
		print 'Committing batchsheet...'
		exp.commit_batchsheet(args.coder)

	elif args.action == 'updateaccounts':
		print 'Updating accounts...'
		update_account_data()
		Experiment.export_accounts()

	elif args.action == 'getvideos':
		print 'Syncing videos with server...'
		newVideos = sync_S3(pull=True)

	elif args.action == 'updatesessions':
		print 'Updating session and coding data...'
		exp.update_session_data()
		exp.update_coding(display=False)

	elif args.action == 'processvideo':
		print 'Processing video...'
		sessionsAffected, improperFilenames, unmatched = exp.update_video_data(reprocess=False, resetPaths=False, display=False)
		assert len(unmatched) == 0
		exp.update_videos_found()
		exp.concatenate_session_videos('all', display=True, replace=False)

	elif args.action == 'update':
		print '\nStarting Lookit update, {:%Y-%m-%d %H:%M:%S}\n'.format(datetime.datetime.now())
		update_account_data()
		Experiment.export_accounts()
		exp.accounts = exp.load_account_data()
		newVideos = sync_S3(pull=True)
		exp.update_session_data()
		exp.update_coding(display=False)
		sessionsAffected, improperFilenames, unmatched = exp.update_video_data(reprocess=False, resetPaths=False, display=False)
		assert len(unmatched) == 0
		exp.update_videos_found()
		exp.concatenate_session_videos('missing', filter={'consent':['yes'], 'withdrawn':[None, False]}, display=True, replace=False)
		print '\nUpdate complete'

	elif args.action == 'makebatches': # TODO: update criteria
		print 'Making batches...'
		exp.make_mp4s_for_study(sessionsToProcess='missing', display=True, trimming=trimLength, suffix='trimmed')
		exp.batch_videos(batchLengthMinutes=batchLengthMinutes, codingCriteria={'consent':['yes'], 'usable':[''], 'withdrawn':[None, False]})

	elif args.action == 'removebatch':
		print 'Removing batch(es)...'
		exp.remove_batch(batchId=args.batchID, batchFilename=args.batchFile, deleteVideos=True)

	elif args.action == 'exportmat':
		coding_export = {}
		for k in exp.coding.keys():
			safeKey = k.replace('.', '_')
			coding_export[safeKey] = exp.coding[k]
		scipy.io.savemat(os.path.join(paths.DATA_DIR, exp.expId + '_coding.mat'), coding_export)

		batches_export = {}
		for k in exp.batchData.keys():
			safeKey = 'b' + k
			batches_export[safeKey] = exp.batchData[k]
		scipy.io.savemat(os.path.join(paths.DATA_DIR, exp.expId + '_batches.mat'), batches_export)

	elif args.action == 'updatevcode':
		#exp.read_batch_coding()
		exp.read_vcode_coding(filter={'consent':['yes'], 'withdrawn':[None, False]})
		exp.summarize_results()

	elif args.action == 'updatevideodata':
		sessionsAffected, improperFilenames, unmatched = exp.update_video_data(newVideos='all', reprocess=True, resetPaths=False, display=False)

	elif args.action == 'tests':
		#sessionsToProcess = ['lookit.session57bc591dc0d9d70055f775dbs.57ddba23c0d9d70060c67d14',
		#					  'lookit.session57bc591dc0d9d70055f775dbs.57ddd64ac0d9d70060c67dd8',
		#					  'lookit.session57bc591dc0d9d70055f775dbs.57de081fc0d9d70061c67e39',
		#					  'lookit.session57bc591dc0d9d70055f775dbs.57ec14a6c0d9d70060c68595',
		#					  'lookit.session57bc591dc0d9d70055f775dbs.57eae5cac0d9d70061c684e2',
		#					  'lookit.session57bc591dc0d9d70055f775dbs.57ea1af0c0d9d70061c684b5']
		#exp.concatenate_session_videos(sessionsToProcess, display=True, replace=False)
		#exp.concatenate_session_videos('all', filter={'consent':['yes'], 'withdrawn':[None, False]}, display=True, replace=True)
		#exp.summarize_results()
		#
		#sessions = ['lookit.session57bc591dc0d9d70055f775dbs.57e68be1c0d9d70061c682da',
		#			 'lookit.session57bc591dc0d9d70055f775dbs.57e70cfbc0d9d70061c68364']
		#exp.concatenate_session_videos(sessions, filter={}, display=True, replace=False)

		#printer.pprint(exp.videoData)
		#printer.pprint(exp.coding)
		#exp.sync_coding_data('coding_data_57bc591dc0d9d70055f775db_kms.bin')
		#sessions = ['lookit.session57bc591dc0d9d70055f775dbs.57dd71bcc0d9d70061c67bec']
		#exp.concatenate_session_videos(sessions, filter={}, display=True, replace=True)
		pass
