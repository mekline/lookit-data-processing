import sysconfig
import os
import errno
import pickle
from client import Account, ExperimenterClient
from sendgrid_client import EmailPreferences, SendGrid
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
from updatefromlookit import sync_S3, pull_from_wowza, update_account_data, update_session_data
import csv
import random
import string
import argparse
import unittest

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
	def make_mp4s(cls, sessDirRel, vidNames, display=False, trimming=False, suffix='',
		replace=False, whichFrames=[]):
		''' Convert flvs in VIDEO_DIR to mp4s organized in SESSION_DIR for a
		particular session

			sessDirRel: relative path to session directory where mp4s
				should be saved. mp4s will be created in
				paths.SESSION_DIR/sessDirRel.

			vidNames: list of video names (flv filenames within
				VIDEO_DIR, also keys into videoData) to convert

			display: whether to display information about progress

			trimming: False (default) not to do any trimming of video
				file. Negative number to specify a maximum clip duration in seconds:
				the last -trimming seconds (counted from the end of the
				shortest stream--generally video rather than audio)
				will be kept, or if the video is shorter than
				trimming, the entire video will be kept. Positive number to specify
				a start point in the video, from the start of audio and video streams.
				Can also provide a vector, of hte same length of vidNames, of
				positive or negative numbers (can be mixed) to specify trim values per
				clip.

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

		# Expand a single 'trimming' value into a vector if needed
		doTrimming = bool(trimming) and not(type(trimming) == list and len(trimming) == 1 and not trimming[0])
		if doTrimming:
			if type(trimming) in [int, float]:
				trimming = [trimming] * len(vidNames)
			else:
				if not(len(vidNames) == len(trimming)):
					print trimming
					print vidNames
					raise ValueError("Must provide a single trimming value or vector of same length as vidNames")

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
				#if display:
				#	print "Already have {} mp4 for video {}, skipping".format(suffix, vid)
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
			# For negative trim values, take the last -trimming[iVid] s. For
			# positive trim values, start from trimming[iVid].
			if doTrimming:
				if trimming[iVid] < 0:
					startTimeVideo = max(0, origDur + trimming[iVid])
					startTimeAudio = max(0, origDur + trimming[iVid])
				else:
					startTimeVideo = trimming[iVid]
					startTimeAudio = trimming[iVid]
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
					if doTrimming:
						print "Starting at time: {}".format(trimming[iVid])


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
	def export_accounts(cls, expId='all'):
		'''Create a .csv sheet showing all account data.

		All fields except password and profiles will be included. Instead of the list of child
		profile dicts under 'profiles', the individual dicts will be expanded as
		child[N].[fieldname] with N starting at 0.

		The current contact settings (SendGrid unsubscribe groups) will also be included
		as okayToSend.[groupname]. TRUE means the user has (at the time of export) NOT unsubscribed.

		If an expId is provided, then only users who have participated at least once in
		the given study will be exported, and the filename will include the expId.
		'''
		cls.load_account_data() # since this may be called without initializing an instance

		# Get SendGrid object & unsubscribe group for notifications
		sg = SendGrid()
		unsubgroups = {}
		for (groupName, group) in sg.groups().items():
			unsubgroups[groupName] = sg.unsubscribes_for(group)

		accs = []
		headers = set()
		allheaders = set()
		for (userid, acc) in cls.accounts.items():
			thisAcc = acc['attributes']
			thisAcc['meta.created-on'] = acc['meta']['created-on']
			thisAcc['username'] = userid
			profiles = thisAcc['profiles']
			del thisAcc['profiles']
			del thisAcc['password']
			for (groupName, unsubscribedList) in unsubgroups.items():
				thisAcc['okayToSend.' + groupName] = not (thisAcc['email'] in unsubscribedList)
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
		initialHeaders = [u'username', u'meta.created-on', u'email',
		                  u'okayToSend.personalCommunication']
		childHeaders = allheaders - headers
		headers = list(headers - set(initialHeaders))
		headers.sort()
		childHeaders = list(childHeaders)
		childHeaders.sort()
		headerList = initialHeaders + headers + childHeaders
		headerList = [h.encode('utf-8') for h in headerList]

		# Order accounts based on date created
		accs.sort(key=lambda b: b['meta.created-on'])

		# Filter if needed to show only participants for this study
		if not expId=='all':
		    thisExp = Experiment(expId)
		    thisExpUsers = [sess['attributes']['profileId'].split('.')[0] for sess in thisExp.sessions['sessions']]

		    accs = [acc for acc in accs if acc['username'] in thisExpUsers]

		# Back up any existing accounts csv file by the same name, & save
		accountsheetPath = paths.accountsheet_filename(expId)
		backup_and_save_dict(accountsheetPath, accs, headerList)

	def __init__(self, expId, trimLength=None):
		self.expId = expId
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
			recompute framerate/duration.
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

			# If it's a consent video, copy it to a separate consent directory
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
					thisVideo = {}

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
			number of seconds, or an event name suffix (string).
			If a number of seconds is given: positive numbers indicate how much
			to trim from the START of the video; negative numbers indicate where
			to start relative to the END of the video (counted from the end of the
			shortest stream - generally video rather than audio; if the video is
			shorter than that, the entire video will be kept). If a string is given,
			then we look for the FIRST occurrence of an even ending in that string
			during this video
			and start from that streamTime (or from the start of the video if the
			event isn't found).

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

			trimmingList = []

			# sess = self.find_session(self.sessions, sessKey)
			# expData = self.sessions['sessions'][iSess]['attributes']['expData']

			for (iVid, vids) in enumerate(self.coding[sessKey]['videosFound']):
				vidNames = vidNames + vids

				if len(vids) > 1:
					warn('Multiple videos found!') # TODO: expand warning

				# If an event name was specified for trimming, also build the appropriate list of
				# trimming values for this session.
				if type(trimming) == str:
					# for (frameId, frameData) in expData.iteritems(): # TODO: remove
					#	  if 'videoId' in frameData.keys():
					#		  allEvents = [e['eventType'] for e in frameData['eventTimings']]
					theseEventTimes = [e['streamTime'] for e in self.coding[sessKey]['allEventTimings'][iVid] if e['eventType'].endswith(trimming)]
					if not theseEventTimes:
						warn('No event found to use for trimming') # TODO: expand warning
						trimmingList = trimmingList + [False] * len(vids)
					else:
						trimmingList = trimmingList + [min(theseEventTimes)] * len(vids)

			if type(trimming) == str:
				sessionTrimming = trimmingList
			else:
				sessionTrimming = trimming

			# Choose a location for the concatenated videos
			sessDirRel = os.path.join(self.expId, sessId)
			sessionDir = os.path.join(paths.SESSION_DIR, sessDirRel)
			make_sure_path_exists(sessionDir)

			# Convert each flv clip to mp4 & get durations

			if display:
				print 'Session: ', sessId

			replace = sessionsToProcess == 'all'

			mp4Data = self.make_mp4s(sessDirRel, vidNames, display, trimming=sessionTrimming,
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

	def concatenate_session_videos(self, sessionKeys, filter={}, replace=False,
		display=False, useTrimmedFrames=[], skipIfEndedEarly=False,
		doPhysicsProcessing=False):
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

		useTrimmedFrames: list of substrings of frame names for which trimmed frames should be used
			(e.g. ['pref-phys-videos'])

		skipIfEndedEarly: whether to omit from concatenated videos any where the coding
			record indicates the video was ended early (e.g. by pausing)

		doPhysicsProcessing: store a few fields in coding specific to physics videos,
			concatVideosShown and concatShowedAlternate

		For each session, this: - uses videosFound in the coding file to
			locate (after creating if necessary) single-clip mp4s
			with text labels - creates a concatenated mp4 with all video for
			this session (in order) in SESSION_DIR/expId/sessId/, called
			expId_sessId.mp4

		Saves expectedDuration and actualDuration to coding data. '''

		print "Making concatenated session videos for study {}".format(self.expId)

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
				#if display:
				#    print "Skipping, already have concat file: {}".format(concatFilename)
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
			if skipIfEndedEarly:
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

			if doPhysicsProcessing:
				vidsShown = [self.coding[sessKey]['videosShown'][vid[1]] for vid in vidData]
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

	def update_coding(self, display=False, doPhysicsProcessing=False):
		'''Update coding data with empty records for any new sessions in saved session
		data, which video files are expected, withdrawn status, & birthdates.

		doPhysicsProcessing additionally updates coding fields showedAlternate,
		endedEarly, and videosShown based on events stored in pref-phys-videos frames.'''

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

			# Get list of video files expected & unique events
			self.coding[sessId]['videosExpected'] = []
			self.coding[sessId]['uniqueEventsOrdered'] = []
			self.coding[sessId]['allEventTimings'] = []
			for (frameId, frameData) in expData.iteritems():
				if 'videoId' in frameData.keys():
					self.coding[sessId]['videosExpected'].append(frameData['videoId'])
					allEvents = [e['eventType'] for e in frameData['eventTimings']]
					allEventsDeDup = []
					for e in allEvents:
						if e not in allEventsDeDup:
							allEventsDeDup.append(e)
					self.coding[sessId]['uniqueEventsOrdered'].append(allEventsDeDup)
					self.coding[sessId]['allEventTimings'].append(frameData['eventTimings'])

			# Processing based on events - specific to physics
			if doPhysicsProcessing:
				self.coding[sessId]['videosExpected'] = []
				self.coding[sessId]['showedAlternate'] = []
				self.coding[sessId]['endedEarly'] = []
				self.coding[sessId]['videosShown'] = []
				for (frameId, frameData) in expData.iteritems():
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
			birthdate = childData[0]['birthday'] if len(childData) else None

			# Compute ages based on registered and exit birthdate
			testdate = datetime.datetime.strptime(testdate[:10], '%Y-%m-%d')

			if not(birthdate == None):
				birthdate = datetime.datetime.strptime(birthdate[:10], '%Y-%m-%d')
				self.coding[sessId]['ageRegistration'] = float((testdate - birthdate).days) * 12.0/365
			else:
				self.coding[sessId]['ageRegistration'] = None

			if exitbirthdate:
				exitbirthdate = datetime.datetime.strptime(exitbirthdate[:10], '%Y-%m-%d')
				self.coding[sessId]['ageExitsurvey'] = float((testdate - exitbirthdate).days) * 12.0/365

		backup_and_save(paths.coding_filename(self.expId), self.coding)

		if display:
			printer.pprint(self.coding)

		print "Updated coding with {} new records for experiment: {}".format(len(newCoding), self.expId)

	def generate_codesheet(self, coderName, showOtherCoders=True, showAllHeaders=False,
	includeFields=[], studyFields=[], excludeFields=[], filter={}, ignoreProfiles=[],
	videoFrameName='', nStudyVideosExpected=0):
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

		studyFields: list of exact field names to include beyond basic headers.

		excludeFields: list of field ENDINGS to exclude.
			For each session, any field ENDING in a string in this list will
			be excluded.

		filter: dictionary of header:[value1, value2, ...] pairs that should be required in
			order for the session to be included in the codesheet. Only records
			with a value in the list for this header will be shown. (Most
			common usage is {'consent':['yes']} to show only records we have
			already confirmed consent for.) This is applied AFTER flattening
			the dict and looking for includeFields above, so it's possible to use
			just the ending of a field if it's also in includeFields. Use 'None' in the
			lists to allow records that don't have this key.

		ignoreProfiles: list of profile IDs not to show, e.g. for test accounts

		videoFrameName: substring of frame to expect video for. Used to compute number
			 of trials with video expected/available.

		nStudyVideosExpected: number of study videos to expect if entire study is
			completed.

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
			if len(childData):
				for (k,v) in childData[0].items():
					childDataLabeled['child.' + k] = v
			else:
				childDataLabeled['child.profileId'] = profile
			val.update(childDataLabeled)

			# Look for fields that end in any of the suffixes in includeFields.
			# If one is found, move the data from that field to the corresponding
			# member of includeFields.
			for fieldEnd in includeFields:
				for field in val.keys():
					if field[-len(fieldEnd):] == fieldEnd:
						val[fieldEnd] = val[field]
						del val[field]

			# Look for fields that end in any of the suffixes in excludeFields.
			# If one is found, remove that data.
			for fieldEnd in excludeFields:
				for field in val.keys():
					if field[-len(fieldEnd):] == fieldEnd:
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
		headerStart = headerStart + ['attributes.feedback',
			'attributes.hasReadFeedback', 'attributes.completed', 'nVideosExpected',
			'nVideosFound', 'expectedDuration', 'actualDuration'] + includeFields + \
			studyFields + \
			['videosExpected', 'videosFound',
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

		# 1. How many unique participants & how many total records?
		profileIds = [sess['child.profileId'] for sess in codingList]
		print "Number of participants: {} unique ({} total records)".format(len(list(set(profileIds))), len(codingList))

		# 2. How many have completed consent at all?
		hasVideo = [sess['child.profileId'] for sess in codingList if sess['nVideosExpected'] > 0]
		print "Completed consent: {} participants ({} records)".format(len(list(set(hasVideo))), len(hasVideo))
		for sess in codingList:
			vidsFound = [v for outer in sess['videosFound'] for v in outer]
			sess['nStudyVideo'] = len([1 for v in vidsFound if videoFrameName in v])
		consentSess = [sess for sess in codingList if sess['consent'] == 'yes']
		nonconsentSess = [sess for sess in codingList if sess['consent'] != 'yes']

		# 3. How many have at least one valid consent?
		print "Valid consent: {} participants ({} records)".format(
			len(list(set([sess['child.profileId'] for sess in consentSess]))),
			len(consentSess))
		print "\trecords: no study videos {}, some study videos {}, entire study {} ({} unique)".format(
			len([1 for sess in consentSess if sess['nStudyVideo'] == 0]),
			len([1 for sess in consentSess if 0 < sess['nStudyVideo'] < nStudyVideosExpected]),
			len([1 for sess in consentSess if sess['nStudyVideo'] >= nStudyVideosExpected]),
			len(list(set([sess['child.profileId'] for sess in consentSess if sess['nStudyVideo'] >= nStudyVideosExpected]))))

		print "Usability (for {} valid consent + some study video records):".format(len([1 for sess in consentSess if sess['nStudyVideo'] > 0]))
		display_unique_counts([sess['usable'] for sess in consentSess if sess['nStudyVideo'] > 0])

		print "Number of usable sessions per participant:"
		display_unique_counts([sess['child.profileId'] for sess in consentSess if sess['usable'] == 'yes'])

		print "Number of total sessions per participant:"
		display_unique_counts([sess['child.profileId'] for sess in consentSess if sess['consent'] == 'yes'])

		print "Privacy: data from {} records with consent. \n\twithdrawn {}, private {}, scientific {}, public {}".format(
			len([sess for sess in consentSess if 'exit-survey.withdrawal' in sess.keys()]),
			len([sess for sess in consentSess if sess.get('exit-survey.withdrawal', False)]),
			len([sess for sess in consentSess if not sess.get('exit-survey.withdrawal', False) and sess.get('exit-survey.useOfMedia', False) == 'private']),
			len([sess for sess in consentSess if not sess.get('exit-survey.withdrawal', False) and sess.get('exit-survey.useOfMedia', False) == 'scientific']),
			len([sess for sess in consentSess if not sess.get('exit-survey.withdrawal', False) and sess.get('exit-survey.useOfMedia', False) == 'public']))

		print "Databrary: data from {} records with consent. \n\tyes {}, no {}".format(
			len([sess for sess in consentSess if 'exit-survey.databraryShare' in sess.keys()]),
			len([sess for sess in consentSess if sess.get('exit-survey.databraryShare', False) == 'yes']),
			len([sess for sess in consentSess if sess.get('exit-survey.databraryShare', False) == 'no']))

		# 4. How many participants have NO valid consent?
		print "No valid consent: {} participants ({} invalid consent records total)".format(
			len(list(set([sess['child.profileId'] for sess in nonconsentSess]) - set([sess['child.profileId'] for sess in consentSess]))),
			len(nonconsentSess))

		print "Nonconsent values:"
		display_unique_counts([sess['consent'] for sess in nonconsentSess])

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

		# Save coding data
		backup_and_save(paths.coding_filename(self.expId), self.coding)


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
correct study on Lookit) or a nickname you'll be told (e.g. 'physics'). Coding sheets
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

To view all current coding:
	python coding.py fetchcodesheet --coder all
	python coding.py fetchconsentsheet --coder all

	Using --coder all will show coder-specific fields from all coders.

To change the list of coders:
	change in .env file. You won't be able to generate a new coding sheet for
	a coder removed from the list, but existing data won't be affected.

To change what fields coders enter in their coding sheets:
	edit coderFields in Experiment (in coding.py), then update coding.
	(python coding.py updatesessions --study study)

	New fields will be added to coding records the next time coding is
	updated. If an existing codesheet is committed before coding is updated OR a
	new coder sheet is created, a warning will be displayed that an expected field is
	missing.

To check for missing video:
	Look at a coding sheet -- can see nVideosExpected and nVideosFound fields.

To look for and process VCode files:
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

	standardExclude = [	 'meta.created-by',
						 'meta.modified-by',
						 'meta.modified-on',
						 'meta.permissions',
						 'relationships.history.links.related',
						 'relationships.history.links.self',
						 'attributes.permissions',
						 'attributes.experimentVersion',
						 'allEventTimings']

	includeFieldsByStudy = {'57a212f23de08a003c10c6cb': [],
							'57adc3373de08a003fb12aad': [],
							'57dae6f73de08a0056fb4165': standardFields,
							'57bc591dc0d9d70055f775db': standardFields,
							'583c892ec0d9d70082123d94': standardFields,
							'58cc039ec0d9d70097f26220': standardFields}

	studyFieldsByStudy = {'583c892ec0d9d70082123d94': ['videosShown', 'showedAlternate', 'endedEarly'],
						  '58cc039ec0d9d70097f26220': ['uniqueEventsOrdered']}

	excludeFieldsByStudy = {'58cc039ec0d9d70097f26220': ['eventTimings'] + standardExclude,
							'583c892ec0d9d70082123d94': standardExclude}

	trimLengthByStudy = {'583c892ec0d9d70082123d94': -20,
						 '58cc039ec0d9d70097f26220': ':startCalibration'}

	videoFramesByStudy = {	'583c892ec0d9d70082123d94': 'pref-phys-videos',
							'58cc039ec0d9d70097f26220': 'alt-trials'}

	nVideosExpByStudy = {  '583c892ec0d9d70082123d94': 24,
							'58cc039ec0d9d70097f26220': 4}

	onlyMakeConcatIfConsent = {	 '583c892ec0d9d70082123d94': True,
							'58cc039ec0d9d70097f26220': False}

	# TODO: combine the above into a 'settings' field

	# Fields required for each action
	actions = {'fetchcodesheet': ['coder', 'study'],
			   'commitcodesheet': ['coder', 'study'],
			   'fetchconsentsheet': ['coder', 'study'],
			   'commitconsentsheet': ['coder', 'study'],
			   'sendfeedback': ['study'],
			   'updateaccounts': [],
			   'updatecoding': ['study'],
			   'getvideos': [],
			   'updatesessions': ['study'],
			   'processvideo': ['study'],
			   'update': ['study'],
			   'updatevcode': ['study'],
			   'export': ['study'],
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
		trimLength = trimLengthByStudy.get(args.study, False)
		exp = Experiment(args.study, trimLength)
		includeFields = includeFieldsByStudy.get(args.study, [])
		excludeFields = excludeFieldsByStudy.get(args.study, [])
		studyFields	  = studyFieldsByStudy.get(args.study, [])
		videoFrameName = videoFramesByStudy.get(args.study, '')
		nVideosExp	  = nVideosExpByStudy.get(args.study, 0)
		doConcatForAll = not(onlyMakeConcatIfConsent.get(args.study, True))

	### Process individual actions

	if args.action == 'sendfeedback':
		print 'Sending feedback...'
		exp.send_feedback()

	elif args.action == 'fetchcodesheet':
		print 'Fetching codesheet...'
		exp.generate_codesheet(args.coder,
			filter={'consent':['yes'], 'exit-survey.withdrawal': [False, None], 'usable':['yes']},
			showAllHeaders=False,
			includeFields=includeFields,
			ignoreProfiles=ignoreProfiles,
			excludeFields=excludeFields,
			studyFields=studyFields,
			videoFrameName=videoFrameName,
			nStudyVideosExpected=nVideosExp)

	elif args.action == 'fetchconsentsheet':
		print 'Fetching consentsheet...'
		exp.generate_codesheet(args.coder,
			filter={'nVideosExpected': range(0,100)},
			showAllHeaders=True,
			includeFields=includeFields,
			excludeFields=excludeFields,
			ignoreProfiles=ignoreProfiles,
			studyFields=studyFields,
			videoFrameName=videoFrameName,
			nStudyVideosExpected=nVideosExp)

		#'consent': ['yes'], 'withdrawn': [False], 'exit-survey.useOfMedia': ['public']

	elif args.action == 'commitcodesheet':
		print 'Committing codesheet...'
		exp.commit_coding(args.coder)

	elif args.action == 'commitconsentsheet':
		print 'Committing consentsheet...'
		exp.commit_global(args.coder, args.fields)

	elif args.action == 'updateaccounts':
		print 'Updating accounts...'
		update_account_data()
		whichStudy = args.study if args.study else 'all'
		print 'Exporting for ' + whichStudy
		Experiment.export_accounts(expId=whichStudy)

	elif args.action == 'getvideos':
		print 'Syncing videos with server...'
		newVideos = sync_S3(pull=True)

	elif args.action == 'updatesessions':
		print 'Updating session and coding data...'
		exp.update_session_data()
		exp.update_coding(display=False, doPhysicsProcessing=(args.study=='583c892ec0d9d70082123d94'))

	elif args.action == 'updatecoding':
		print 'Updating coding data...'
		exp.update_coding(display=False, doPhysicsProcessing=(args.study=='583c892ec0d9d70082123d94'))

	elif args.action == 'processvideo':
		print 'Processing video...'
		sessionsAffected, improperFilenames, unmatched = exp.update_video_data(reprocess=False, resetPaths=False, display=False)
		assert len(unmatched) == 0
		exp.update_videos_found()
		exp.concatenate_session_videos('all', display=True, replace=False, useTrimmedFrames=[videoFrameName],
			skipIfEndedEarly=(args.study=='583c892ec0d9d70082123d94'),
			doPhysicsProcessing=(args.study=='583c892ec0d9d70082123d94'))

	elif args.action == 'update':
		print '\nStarting Lookit update, {:%Y-%m-%d %H:%M:%S}\n'.format(datetime.datetime.now())
		update_account_data()
		Experiment.export_accounts()
		exp.accounts = exp.load_account_data()
		newVideos = sync_S3(pull=True)
		exp.update_session_data()
		exp.update_coding(display=False, doPhysicsProcessing=(args.study=='583c892ec0d9d70082123d94'))
		sessionsAffected, improperFilenames, unmatched = exp.update_video_data(reprocess=False, resetPaths=False, display=False)
		assert len(unmatched) == 0
		exp.update_videos_found()
		if doConcatForAll:
			exp.concatenate_session_videos('missing', filter={'withdrawn':[None, False]}, display=True, replace=False, useTrimmedFrames=[videoFrameName],
			skipIfEndedEarly=(args.study=='583c892ec0d9d70082123d94'),
			doPhysicsProcessing=(args.study=='583c892ec0d9d70082123d94'))
		else:
			exp.concatenate_session_videos('missing', filter={'consent':['yes'], 'withdrawn':[None, False]}, display=True, replace=False, useTrimmedFrames=[videoFrameName],
			skipIfEndedEarly=(args.study=='583c892ec0d9d70082123d94'),
			doPhysicsProcessing=(args.study=='583c892ec0d9d70082123d94'))
		print '\nUpdate complete'

	elif args.action == 'updatevcode':
		exp.read_vcode_coding(filter={'consent':['yes'], 'withdrawn':[None, False]})
		exp.summarize_results()

	elif args.action == 'updatevideodata':
		sessionsAffected, improperFilenames, unmatched = exp.update_video_data(newVideos='all', reprocess=True, resetPaths=False, display=False)

	elif args.action == 'export':
		for sessKey, sessCoding in exp.coding.items():
			if sessCoding['consent'] == 'yes' and not sessCoding['withdrawn']:
				sessData = exp.find_session(exp.sessions, sessKey)
				exitSurveyName = '33-33-exit-survey' if '33-33-exit-survey' in sessData['attributes']['expData'].keys() else '32-32-exit-survey'
				privacy = 'private' if not(sessData['attributes']['completed']) else sessData['attributes']['expData'][exitSurveyName]['useOfMedia']
				childId = sessData['attributes']['profileId'][-5:]
				print (sessKey, privacy, childId)
				shortKey = paths.parse_session_key(sessKey)[1]
				mp4Path = os.path.join(paths.SESSION_DIR, exp.expId, shortKey, exp.expId + '_' + shortKey + '.mp4')
				print mp4Path
				exportDir = os.path.join(paths.EXPORT_DIR, exp.expId)
				make_sure_path_exists(exportDir)
				exportPath = os.path.join(exportDir, exp.expId + '_' + childId + '_' + shortKey + '_' + privacy + '.mp4')
				print exportPath
				sp.call(['cp', mp4Path, exportPath])
