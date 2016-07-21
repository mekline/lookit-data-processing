import os
import videoutils
import subprocess as sp

origPath = '/Users/kms/lookitkim/scripts/testvideo'
vidNames = ['v1.flv', 'v2.flv', 'v3.flv', 'v4.flv', 'v5.flv', 'v6.flv', 'v7.flv']

vidDurs = {}
concat = ['ffmpeg']
inputList = ''
totalDur = 0
loglevel = 'warning'

for (iVid, vid) in enumerate(vidNames):
	vidPath = os.path.join(origPath, 'orig', vid)

	noAudioPath = os.path.join(origPath, 'mp4', vid[:-4] + '_trimmed.mp4')
	sp.call(['ffmpeg', '-i', vidPath, '-filter_complex',
   "[0:v]drawtext='fontfile=/Library/Fonts/Arial Black.ttf':text='abc':fontsize=12:fontcolor=red:x=10:y=10,setpts=PTS-STARTPTS[v0]", '-map', '[v0]', '-c:v', 'libx264', '-an', '-vsync', 'cfr', '-r', '30', '-crf', '18', noAudioPath, '-loglevel', loglevel])

	audioPath = os.path.join(origPath, 'mp4', vid[:-4] + '_audio.m4a')
	sp.call(['ffmpeg', '-i', vidPath, '-vn', '-filter_complex', '[0:a]apad=pad_len=100000', '-c:a', 'libfdk_aac', '-loglevel', loglevel, audioPath])

	mergedPath = os.path.join(origPath, 'mp4', vid[:-4] + '_merged.mp4')
	sp.call(['ffmpeg', '-i', noAudioPath, '-i', audioPath, '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-loglevel', loglevel, mergedPath])
	mp4Path = mergedPath

	(height, width, nFrames, dur, bitRate, startTime) = videoutils.get_video_details(mp4Path, fullpath=True, getVidStart=True)
	print (startTime, dur)
	vidDurs[vid] = dur
	totalDur = totalDur + dur

	# Add to concatenate command
	concat = concat + ['-i', mp4Path]
	inputList = inputList + '[{}:0][{}:1]'.format(iVid, iVid)

print 'expected total dur: ', totalDur

# Concatenate mp4 videos
concat = concat + ['-filter_complex', inputList + 'concat=n={}:v=1:a=1'.format(len(vidNames)) + '[out]', '-map', '[out]', os.path.join(origPath, 'mp4', 'concat.mp4'), '-loglevel', loglevel]
sp.call(concat)

(height, width, nFrames, dur, bitRate, startTime) = videoutils.get_video_details(os.path.join(origPath, 'mp4', 'concat.mp4'), fullpath=True, getVidStart=True)
print 'actual total dur: ', dur
