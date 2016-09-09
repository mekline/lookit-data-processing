import unittest
from utils import printer
import numpy as np
import warnings

def read_preferential(vcodepath, whichTrials=[], lastTrialLength=[], interval=[], videoLengths=[]):
    '''Reads preferential looking data from a VCode text file

     Usage:
     (durations, leftLookTime, rightLookTime, oofTime) = ...
        read_preferential(filename, interval=[], lastTrialLength=[], whichTrials=[],
        videoLengths=[])
       filename: full path to the VCode text file
       interval: section of each trial to use. Options:
         []: use whole trial
         [msA, msB]: use from (trialStart + msA) to (trialStart + msB); e.g.
             set this to [2000, 6000] to use from second 2 to second 6.
         [msA, 0]: use the period from (trialEnd + msA) to trialEnd; e.g. set
             this to [-5000, 0] to use the last five seconds of the trial
       lastTrialLength: minimum length of last trial to assume (if supplied, VCode file
         is expected to have trial markers only at the start of each trial). Default [];
         if empty, VCode file is expected to have an extra trial marker which marks the
         end of the last trial.
       whichTrials: Only computes looking times and msArray for the trials
         specified in whichTrials. If whichTrials is empty, all are used.
         Output variables are still indexed by trial (rather than index into
         whichTrial) and non-whichTrials values are 0.
       videoLengths: If given, override any trial markers and instead use the list of
         video lengths (in seconds) to determine trial boundaries. VCode file is expected
         to have one event 'end' which marks the end of the trial, and trial lengths are
         scaled accordingly.

      Return values:

      durations: array of durations of trials (in ms)

      leftLookTime: array of ms coded as 'left' per trial, indexed
         by trial number; only valid for non-looking-time trials

      leftLookTime: array of ms coded as 'right' per trial, indexed
         by trial number; only valid for non-looking-time trials

      oofTime: array of ms coded as 'right' per trial, indexed
         by trial number; only valid for non-looking-time trials


    Expects a VCode file with trial types 'trial', 'left', 'right', 'away',
      and possibly 'outofframe'. Marks with 'x' or 'delete'
     notes will be ignored. Some misspellings are allowed (see start of
     function) and 'looking', 'nosound' are accepted but not used.

     Where a child is looking can be determined from these marks: if it's in
     an 'outofframe' mark, we can't tell because we can't see the child's
     eyes. If the current frame has mark X or the most recent mark is X, then
     the child is looking at X (where X may be left, right, or away). Marks
     during outofframe are still used to determine where the child is looking
     once the outofframe event ends.'''

    trialNames = ['trial', 'trials', 'trail', 'trails']
    leftNames = ['left']
    rightNames = ['right']
    awayNames = ['away']
    outofframeNames = ['outofframe', 'outoframe', 'outoffame']
    deleteNames = ['x', 'delete']
    otherNames = ['looking', 'look', 'looking time', 'nosound', 'sound']
    endNames = ['end']

    # Read the file
    f = open(vcodepath, 'r')
    lines = f.readlines()[4:]
    f.close()

    # Each line is in the format start, duration, type, mark\n
    codemarks = []
    for line in lines:
        pieces = line.strip().split(',')
        m = {'start': int(pieces[0]), 'duration': int(pieces[1]), 'type': pieces[2], 'mark': pieces[3]}
        codemarks.append(m)

    # Sort by start time and delete ones marked as deleted
    codemarks.sort(key=lambda m: m['start'])
    codemarks = [m for m in codemarks if m['mark'] not in deleteNames]

    # Make lists of start time, code type, and marks
    starts = np.array([m['start'] for m in codemarks])
    durations = np.array([m['duration'] for m in codemarks])
    types = np.array([m['type'].strip().lower() for m in codemarks])
    marks = np.array([m['mark'].strip().lower() for m in codemarks])

    # Warn about any unknown mark types (could be typos we should add)
    unknownTypes = set(types) - set(trialNames + leftNames + rightNames + awayNames + outofframeNames + deleteNames + otherNames + endNames)
    if unknownTypes:
        for t in unknownTypes:
            warnings.warn('Unknown mark type: {}'.format(t))

    # Warn if no trials or no looks are detected
    if not np.any([t in trialNames for t in types]) and not videoLengths:
        warnings.warn('No trials detected in file {}'.format(vcodepath))
    if not np.any([t in (leftNames + rightNames + awayNames) for t in types]):
        warnings.warn('No looks right/left/away detected in file {}'.format(vcodepath))

    trialInds   = np.array([t in trialNames for t in types])
    leftInds    = np.array([t in leftNames for t in types])
    rightInds   = np.array([t in rightNames for t in types])
    awayInds    = np.array([t in awayNames for t in types])
    oofInds     = np.array([t in outofframeNames for t in types])
    endInds     = np.array([t in endNames for t in types])
    allLookInds = np.logical_or(leftInds, np.logical_or(rightInds, awayInds))
    allLooks    = starts[np.nonzero(allLookInds)]

    allLookTypes = 1 * leftInds.astype(int) + \
                   2 * rightInds.astype(int) + \
                   3 * awayInds.astype(int)
    allLookTypes = [look for look in allLookTypes if look > 0]
    # indices into allLooks and allLookTypes are the same (looks only)

    # Adjust looking times based on out-of-frame coding
    oofStarts = starts[np.nonzero(oofInds)]
    oofEnds   = oofStarts + durations[np.nonzero(oofInds)]

    for iOof in range(len(oofStarts)):
        # Where is the child looking at the END of this period?
        looks = np.nonzero(allLooks <= oofEnds[iOof])[0]
        lastLookType = 3 if not len(looks) else allLookTypes[looks[-1]]

        # Delete any marks within the period
        removeInds = np.nonzero(np.logical_and(allLooks >= oofStarts[iOof], \
                                               allLooks <= oofEnds[iOof]))

        allLooks = np.delete(allLooks, removeInds)
        allLookTypes = np.delete(allLookTypes, removeInds)

        # And move/copy that mark to the end of the period.
        allLooks = np.concatenate((allLooks, [oofEnds[iOof]]))
        allLookTypes = np.concatenate((allLookTypes, [lastLookType]))

        # Resort so that we can still use "which look comes last" above
        sortInds = np.argsort(allLooks)
        allLooks = allLooks[sortInds]
        allLookTypes = allLookTypes[sortInds]

    # Add OOF events to look array and re-sort
    allLooks = np.append(allLooks, oofStarts)
    allLookTypes = np.append(allLookTypes, 4*np.ones((1,len(oofStarts))))

    sortInds = np.argsort(allLooks)
    allLooks = allLooks[sortInds]
    allLookTypes = allLookTypes[sortInds]

    # Determine trial boundaries to use based on input

    if videoLengths == []:
        trialStarts = starts[trialInds]

        # Infer an extra trial end if lastTrialLength is given
        if not lastTrialLength: # No lastTrialLength: expect a trial marker at the end of the last trial
            lastTrialLength = 0
            trialEnds = trialStarts[1:]
            trialStarts = trialStarts[:-1]
        else:
            trialEnds = np.concatenate((trialStarts[1:], [(trialStarts[-1] + max(lastTrialLength, trialStarts[-1]-trialStarts[-2], trialStarts[-2]-trialStarts[-3]))]))
    else:
        vcodeEnd = starts[endInds]
        if not vcodeEnd.size:
            warnings.warn('{}: No end mark in VCode file! Not scaling to actual length.'.format(vcodepath))
            vcodeEnd = 1000*sum(videoLengths)
        elif vcodeEnd.size > 1:
            warnings.warn('{}: Multiple end marks in VCode file! Using first.'.format(vcodepath))
            vcodeEnd = vcodeEnd[0]
        vcodeEnd = float(vcodeEnd)
        if abs(vcodeEnd - 1000*sum(videoLengths)) > 1000:
            warnings.warn('{}: Large difference between VCode end mark {} and expected length {}'.format(vcodepath, vcodeEnd, 1000*sum(videoLengths)))
        # Add a 0 for start of first trial and convert s -> ms
        trialStarts = np.concatenate(([0], np.multiply(1000,np.cumsum(videoLengths))))
        # Scale to total length vcodeEnd
        trialStarts = np.multiply(vcodeEnd/trialStarts[-1], trialStarts)
        # Make trialStarts an int array
        trialStarts = np.array(np.round(trialStarts), dtype=int)
        # Use first N-1 as starts, last N-1 as ends
        trialEnds = trialStarts[1:]
        trialStarts = trialStarts[:-1]


# %     []: use whole trial
# %     [msA, msB]: use from (trialStart + msA) to (trialStart + msB); e.g.
# %         set this to [2000, 6000] to use from second 2 to second 6.
# %     [msA, 0]: use the period from (trialEnd + msA) to trialEnd; e.g. set
# %         this to [-5000, 0] to use the last five seconds of the trial

    # Use the correct interval
    if len(interval):
        if interval[1]:
            trialStarts = np.minimum(trialEnds, np.add(trialStarts, interval[0]))
            trialEnds = np.minimum(trialEnds, np.add(trialStarts, interval[1]))
        else:
            trialStarts = np.maximum(trialStarts, np.add(trialEnds,  interval[0]))

    durations = np.subtract(trialEnds, trialStarts)

    if not len(whichTrials):
        whichTrials = range(len(durations))

    leftLookTime = np.zeros((len(durations)))
    rightLookTime = np.zeros((len(durations)))
    oofTime = np.zeros((len(durations)))

    for iT in whichTrials:
        startT = trialStarts[iT]
        endT = trialEnds[iT]

        for iLook in range(len(allLooks)-1):
            a = max(allLooks[iLook], startT)
            b = min(allLooks[iLook + 1], endT)

            if b - a > 0:
                if allLookTypes[iLook] == 1: # left look
                    leftLookTime[iT] += b - a
                elif allLookTypes[iLook] == 2: # right look
                    rightLookTime[iT] += b - a
                elif allLookTypes[iLook] == 4: # outofframe (skip away)
                    oofTime[iT] += b - a

    return (durations, leftLookTime, rightLookTime, oofTime)


class TestLookingMethods(unittest.TestCase):

    def test_1(self): # Check that we can use videoLengths w/o changing anything
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_-2child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12934, 7965, 8067, 7700, 12933, 7534, 8033, 8033, 48701, 12967, 8099, 8034, 8099]))
        self.assertTrue(np.all(leftLookTime == [0, 3563, 1900, 2028, 0, 2852, 5000, 2666, 0, 0, 6532, 5084, 0]))
        self.assertTrue(np.all(rightLookTime == [0, 4402, 5399, 5672, 0, 4682, 1382, 5200, 0, 0, 1567, 2066, 0]))
        self.assertTrue(np.all(oofTime == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
        (durations2, leftLookTime2, rightLookTime2, oofTime2) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_-2child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12], 1), lastTrialLength=8000, interval=[], videoLengths=np.multiply(0.001,durations))
        self.assertTrue(np.all(durations == durations2))
        self.assertTrue(np.all(leftLookTime == leftLookTime2))
        self.assertTrue(np.all(rightLookTime == rightLookTime2))
        self.assertTrue(np.all(oofTime == oofTime2))


    def test_2(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_-3child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [13083,8333,8000,8417,13000,8167,8000,8333,44000,13084,8166,8084,8166]))
        self.assertTrue(np.all(leftLookTime == [0,1933,1740,2917,0,3199,3750,3000,0,0,5635,2664,2416]))
        self.assertTrue(np.all(rightLookTime == [0,6400,6260,5500,0,4968,4250,5333,0,0,2531,5420,4510]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_3(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_1441child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12833,8083,7917,8000,12750,7917,7833,8083,44334,12667,8000,8000,8000]))
        self.assertTrue(np.all(leftLookTime == [0,2333,2918,3500,0,2167,1999,4000,0,0,4329,3999,1000]))
        self.assertTrue(np.all(rightLookTime == [0,5750,4332,4500,0,5750,3750,2916,0,0,3667,2835,5083]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_4(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_1464child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12666,7750,7834,8083,12667,8250,7916,7417,44250,12750,8750,7750,8750]))
        self.assertTrue(np.all(leftLookTime == [0,2806,2052,2841,0,3046,3921,4586,0,0,4613,5453,4583]))
        self.assertTrue(np.all(rightLookTime == [0,4944,5667,3419,0,5204,3995,2281,0,0,4137,2297,1667]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_5(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_1472child1.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12666,7834,7666,7750,12584,7916,7750,7834,48250,12583,7750,7834,8000]))
        self.assertTrue(np.all(leftLookTime == [0,1650,1503,833,0,5761,6006,4916,0,0,4017,5658,1333]))
        self.assertTrue(np.all(rightLookTime == [0,6184,5052,6917,0,2155,1744,2918,0,0,3733,2176,2508]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_6(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_1533child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12250,7666,7584,7416,12917,7333,7917,7917,47500,12667,8083,7667,8083]))
        self.assertTrue(np.all(leftLookTime == [0,0,2668,2833,0,2500,2333,2000,0,0,4474,1250,3084]))
        self.assertTrue(np.all(rightLookTime == [0,7666,4916,4583,0,4833,5584,5917,0,0,3609,6417,666]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_7(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_1534child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [14166,8250,9000,7417,15167,7666,8000,8917,45333,13917,9000,8917,9000]))
        self.assertTrue(np.all(leftLookTime == [0,5196,1490,332,0,5920,4764,3504,0,0,6335,6499,4444]))
        self.assertTrue(np.all(rightLookTime == [0,3054,7510,7085,0,1746,3236,5413,0,0,2665,2418,3080]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_8(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_198child2.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12750,7583,7833,8000,12750,7834,7916,8000,48584,12500,8000,7583,8000]))
        self.assertTrue(np.all(leftLookTime == [0,4130,2815,2196,0,6883,6955,2413,0,0,4474,5813,5319]))
        self.assertTrue(np.all(rightLookTime == [0,3453,3943,5255,0,951,961,5587,0,0,3526,1770,869]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_9(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_2173child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12934,7899,7566,7668,12667,7732,8168,7866,41900,12466,7367,7767,8000]))
        self.assertTrue(np.all(leftLookTime == [0,7012,6245,3829,0,2204,866,5357,0,0,1703,1939,1516]))
        self.assertTrue(np.all(rightLookTime == [0,887,1321,3839,0,5528,7302,2509,0,0,5664,5828,1724]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,1968]))

    def test_10(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_2237child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [13199,8767,8068,8033,12899,10034,7933,7933,44601,12900,10032,8101,10032]))
        self.assertTrue(np.all(leftLookTime == [0,1357,867,782,0,5752,6303,5675,0,0,4743,4151,1019]))
        self.assertTrue(np.all(rightLookTime == [0,7410,7201,6282,0,4282,1630,2258,0,0,5289,3950,4542]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_11(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_283child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12333,7583,8000,7750,12750,7584,7833,7417,48666,12501,7833,7667,8000]))
        self.assertTrue(np.all(leftLookTime == [0,1505,0,1908,0,3930,2602,2442,0,0,4284,3262,1436]))
        self.assertTrue(np.all(rightLookTime == [0,6078,8000,5842,0,3349,5231,4975,0,0,3549,2997,6564]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_12(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_3060child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [13166,8601,7899,8068,12966,8399,8000,7968,48833,12734,8466,7900,8466]))
        self.assertTrue(np.all(leftLookTime == [0,5466,2186,2082,0,7128,6282,7968,0,0,4719,1959,3116]))
        self.assertTrue(np.all(rightLookTime == [0,3135,5713,5986,0,568,1718,0,0,0,3747,5941,2758]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

    def test_13(self):
        (durations, leftLookTime, rightLookTime, oofTime) = read_preferential('/Users/kms/lookitkim/scripts/tests/novelverbs_88child0.txt', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])
        self.assertTrue(np.all(durations == [12750,9083,8333,8250,12917,8917,8250,8166,54751,13000,8583,7917,8583]))
        self.assertTrue(np.all(leftLookTime == [0,2665,2386,2345,0,5264,4950,5833,0,0,2358,989,750]))
        self.assertTrue(np.all(rightLookTime == [0,6418,5947,5905,0,3653,3300,2333,0,0,6225,6928,2166]))
        self.assertTrue(np.all(oofTime == [0,0,0,0,0,0,0,0,0,0,0,0,0]))

if __name__ == '__main__':
    unittest.main()
