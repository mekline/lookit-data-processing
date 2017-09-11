import os

def processPhysicsCoding(codingRecord, expData):
	'''Additional processing when updating coding for the physics study.

	Meant to be given as a processingFunction argument to Experimenter.updatecoding.

	codingRecord: a value in the Experiment.coding dictionary

	expData: corresponding session['attributes']['expData'] field for this session; dictionary of frameId: frameData pairs.

	Returns codingRecord, edited in place with the following fields added:
		videosExpected: list of videoIds for any frames in expData with a videoId field. These are not the full filename with timestamp & random string: they just have the study ID, frame ID, and session ID, e.g.,
			'583c892ec0d9d70082123d94_11-pref-phys-videos_58474acfc0d9d70082123db6'
		showedAlternate: corresponding to videosExpected, a list of whether the alternate test video was shown during this trial. True/False for pref-phys-videos frames; None for other frames with video (e.g. consent, video-preview)
		endedEarly: corresponding to videosExpected, a list of whether the trial was ended early, determined as either not having a 'startTestVideo'/'startAlternateVideo' event OR the alternate video was paused OR video was paused but alternate not started.
		videosShown: corresponding to videosExpected, a list of videos shown. If alternate video was shown, the alternate is stored here. Filename (without path/extension) is stored: e.g. u'sbs_stay_near_mostly-on_hammer_c2_green_NN'
	'''

	codingRecord['videosExpected'] = []
	codingRecord['showedAlternate'] = []
	codingRecord['endedEarly'] = []
	codingRecord['videosShown'] = []
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

			codingRecord['videosExpected'].append(frameData['videoId'])
			codingRecord['showedAlternate'].append(showAlternate)
			codingRecord['videosShown'].append(thisVideo)
			codingRecord['endedEarly'].append(endedEarly)

	return codingRecord

def processPhysicsConcat(codingRecord, vidData):
	'''Updates a coding record based on the vidData structure used in concatenate_session_videos.
	Meant to be used as a processingFunction argument to concatenate_session_videos.

	vidData: list of video data; each element is a list
		[vidName, vidInd, vidTimestamp, useWhole].
		vidInd gives the index of this video in codeRecord['videosFound']

	codeRecord: value from coding dictionary, corresponding to this video list.

	Saves concatShowedAlternate and concatVideosShown fields, lists of whether video shown
	was the alternate test video and the video name, respectively, corresponding to the list
	of concatenated videos in vidData.

	updates codeRecord in place and returns.'''

	vidsShown = [codingRecord['videosShown'][vid[1]] for vid in vidData]
	codingRecord['concatShowedAlternate'] = [codingRecord['showedAlternate'][i] for (vidName, i, t, useW) in vidData]
	codingRecord['concatVideosShown'] = vidsShown
	return codingRecord

def skipIfEndedEarly(vidData, codeRecord):
	'''Selects vidData elements correpsonding to only frames that didn't end early.
	Meant to be given as an argument to concatenate_session_videos.

	vidData: list of video data; each element is a list
		[vidName, vidInd, vidTimestamp, useWhole].
		vidInd gives the index of this video in codeRecord['videosFound']

	codeRecord: value from coding dictionary, corresponding to this video list.

	Returns a sublist of vidData, where the corresponding element of codeRecord['endedEarly']
	is False.'''

	return [vid for vid in vidData if not codeRecord['endedEarly'][vid[1]]]

# List of current coder names. coding.py will only create/commit coding for coders on this list. Removing an inactive coder will not affect existing data.
CODERS = ['Jessica', 'Kim', 'Training', 'Realtime', 'Alice']

# Allow usage of study 'nicknames' when calling coding.py or reminder_emails.py
studyNicknames = {'physics': '583c892ec0d9d70082123d94',
				  'test': '57adc3373de08a003fb12aad',
				  'pilot': '57dae6f73de08a0056fb4165',
				  'prodpilot':'57bc591dc0d9d70055f775db',
				  'staging-geometry': '58a769913de08a0040ead68b',
				  'geometry': '58cc039ec0d9d70097f26220'}

# Don't show/count these profile IDs when making coding spreadsheets
ignoreProfiles = ['kim2.smtS6', 'kim2.HVv94', 'bostoncollege.uJG4X', 'sam.pOE5w', 'abought.hqReV']

# Default list of fields endings to include in coding sheets, beyond basic
# headers. For each session, any field ENDING in a string in this list will
# be included. The original field name will be removed and the
# corresponding data stored under this partial name, so they should
# be unique endings within sessions. (Using just the ending allows
# for variation in which segment the field is associated with.)
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

# Default list of field ENDINGS to exclude. For each session, any field ENDING
# in a string in this list will excluded from consent/codesheets.
standardExclude = [		 'allEventTimings',
						 'meta.created-by',
						 'meta.modified-by',
						 'meta.modified-on',
						 'meta.permissions',
						 'relationships.history.links.related',
						 'relationships.history.links.self',
						 'attributes.permissions',
						 'attributes.experimentVersion']

# Default study settings; overridden by any values in settingsByStudy.
settings = {
		'onlyMakeConcatIfConsent': False, # Don't concatenate video unless consent field is 'yes'
		'nVideosExp': 0, # Study videos to expect; for summary display only
		'videoFrameNames': [], # Frame substrings we expect video for; these videos will be trimmed
		'trimLength': False, #For videos we do trimming of: False (default) not to do any trimming of video file, or a number of seconds, or an event name suffix (string). If a number of seconds is given: positive numbers indicate how much to trim from the START of the video; negative numbers indicate where to start relative to the END of the video (counted from the end of the shortest stream - generally video rather than audio; if the video is shorter than that, the entire video will be kept). If a string is given, then we look for the FIRST occurrence of an even ending in that string during this video and start from that streamTime (or from the start of the video if the event isn't found).
		'excludeFields': standardExclude,
		'studyFields': [], # List of exact field names to include in codesheets, beyond basic headers
		'includeFields': standardFields,
		'extraCodingFields': [], # Additional fields to add to coding records
		'codingProcessFunction': None, # Function for additional coding processing - see Experiment.update_coding
		'concatProcessFunction': None, # Function for additional coding processing after video concatenation - see Experiment.concatenate_session_videos
		'concatSkipFunction': None, # Function to select videos for concatenation - see Experiment.concatenate_session_videos
		'eventsToAnnotate': [] # list of event types that should be annotated in bottom left of videos (any events ending in any of these will be annotated)
	}

# For each study using coding.py, add a dictionary entry with studyId/studyNickname:settings here. settings (defined above) are the default values; anything here overrides those.
settingsByStudy = {
		'physics': {
			'onlyMakeConcatIfConsent': True,
			'nVideosExp': 24,
			'videoFrameNames': ['pref-phys-videos'],
			'trimLength': -20,
			'excludeFields': standardExclude,
			'studyFields': ['videosShown', 'showedAlternate', 'endedEarly'],
			'includeFields': standardFields,
			'extraCodingFields': {
				'concatShowedAlternate': None,
				'concatVideosShown': None,
				'videosExpected': [],
				'showedAlternate': [],
				'endedEarly': [],
				'videosShown': []
				},
			'codingProcessFunction': processPhysicsCoding,
			'concatProcessFunction': processPhysicsConcat,
			'concatSkipFunction': skipIfEndedEarly,
			'eventsToAnnotate': ['exp-physics:startIntro',
				'exp-physics:startTestVideo',
				'exp-physics:enteredFullscreen',
				'exp-physics:pauseVideo',
				'exp-physics:leftFullscreen',
				'exp-physics:startAlternateVideo']
		},
		'geometry': {
			'onlyMakeConcatIfConsent': False,
			'nVideosExp': 4,
			'videoFrameNames': ['alt-trials'],
			'trimLength': -72,
			'excludeFields': ['eventTimings'] + standardExclude,
			'studyFields': ['uniqueEventsOrdered'],
			'includeFields': standardFields,
			'eventsToAnnotate': ['exp-alternation:pauseVideo',
				'exp-alternation:unpauseVideo',
				'exp-alternation:startIntro',
				'exp-alternation:startCalibration',
				'exp-alternation:startTestTrial',
				'exp-alternation:enteredFullscreen',
				'exp-alternation:leftFullscreen',
				'exp-alternation:stoppingCapture']
		}
	}

settingsByStudy['prodpilot'] = settingsByStudy['physics']
