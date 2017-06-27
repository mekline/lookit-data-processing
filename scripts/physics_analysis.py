import sysconfig
import os
import errno
import pickle
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

if sysconfig.get_config_var("PYTHONFRAMEWORK"):
	import matplotlib.pyplot as plt
	import numpy as np
	import scipy.stats
else:
	print "Non-framework build: not importing matplotlib. Plotting functionality will raise error."

def summarize_results(Exp):
    '''Summarize some coding results from an Experiment object - for physics studys'''

    usableSessions = {sKey:c for (sKey, c) in Exp.coding.items() if c['usable'][:3] == 'yes'}

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
