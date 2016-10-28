testdir = '/Users/kms/lookitkim/scripts/tests';
testfiles = dir(testdir);

interval = [];
lastTrialLength = 8000;
whichTrials = [2 3 4 6 7 8 11 12 13];

for iFile = 1:length(testfiles)
    name = testfiles(iFile).name;
    if name(1) ~= '.' && strcmp(name(end-3:end), '.txt')
        [durations, leftLookTime, rightLookTime, oofTime] = ...
    read_preferential_vcode(fullfile(testdir, name), interval, lastTrialLength, whichTrials);
        
        fprintf(['(durations, leftLookTime, rightLookTime, oofTime) = read_preferential_vcode(\''/Users/kms/lookitkim/scripts/tests/', ...
            name, '\'', whichTrials=np.subtract([2,3,4,6,7,8,11,12,13], 1), lastTrialLength=8000, interval=[])\r']);

        durations(1) = durations(1) + 1;
        fprintf(1, 'self.assertTrue(np.all(durations == [')
        for i = 1:length(durations)
            if i == length(durations)
                fprintf(1, [num2str(durations(i))]);
            else
                fprintf(1, [num2str(durations(i)) ',']);
            end
        end
        fprintf(']))\r');
        
        fprintf(1, 'self.assertTrue(np.all(leftLookTime == [')
        for i = 1:length(leftLookTime)
            if i == length(leftLookTime)
                fprintf(1, [num2str(leftLookTime(i))]);
            else
                fprintf(1, [num2str(leftLookTime(i)) ',']);
            end
        end
        fprintf(']))\r');
        
        fprintf(1, 'self.assertTrue(np.all(rightLookTime == [')
        for i = 1:length(rightLookTime)
            if i == length(rightLookTime)
                fprintf(1, [num2str(rightLookTime(i))]);
            else
                fprintf(1, [num2str(rightLookTime(i)) ',']);
            end
        end
        fprintf(']))\r');
        
        fprintf(1, 'self.assertTrue(np.all(oofTime == [')
        for i = 1:length(oofTime)
            if i == length(oofTime)
                fprintf(1, [num2str(oofTime(i))]);
            else
                fprintf(1, [num2str(oofTime(i)) ',']);
            end
        end
        fprintf(']))\r\r');
        
    end
end