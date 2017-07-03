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


CODERS = ['Jessica', 'Kim', 'Training', 'Realtime', 'Alice']

studyNicknames = {'physics': '583c892ec0d9d70082123d94',
				  'test': '57adc3373de08a003fb12aad',
				  'pilot': '57dae6f73de08a0056fb4165',
				  'prodpilot':'57bc591dc0d9d70055f775db',
				  'staging-geometry': '58a769913de08a0040ead68b',
				  'geometry': '58cc039ec0d9d70097f26220'}

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
						 'attributes.experimentVersion']

settings = {
        'onlyMakeConcatIfConsent': False,
		'nVideosExp': 0,
		'videoFrameNames': [],
		'trimLength': False,
		'excludeFields': standardExclude,
		'studyFields': [],
		'includeFields': standardFields,
		'doPhysicsProcessing': False,
		'extraCodingFields': [],
		'codingProcessFunction': None,
		'concatProcessFunction': None,
		'concatSkipFunction': None
	}

settingsByStudy = {
		'physics': {
			'onlyMakeConcatIfConsent': True,
			'nVideosExp': 24,
			'videoFrameNames': ['pref-phys-videos'],
			'trimLength': -20,
			'excludeFields': standardExclude,
			'studyFields': ['videosShown', 'showedAlternate', 'endedEarly'],
			'includeFields': standardFields,
			'doPhysicsProcessing': True,
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
			'concatSkipFunction': skipIfEndedEarly
		},
		'geometry': {
			'onlyMakeConcatIfConsent': False,
			'nVideosExp': 4,
			'videoFrameNames': ['alt-trials'],
			'trimLength': ':startCalibration',
			'excludeFields': ['eventTimings'] + standardExclude,
			'studyFields': ['uniqueEventsOrdered'],
			'includeFields': standardFields
		}
	}
