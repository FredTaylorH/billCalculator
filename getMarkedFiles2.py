#!/usr/bin/env python
import os
#sce-Serviceaccount-state-585fa0a9e1eccb16a8e8b8e4.csv
#get utility, target phrase, fieldname

class MasterCsv(object):
    
    def __init__(self,textFile='allcsvs.txt'):
        self.filenames = []
        with open (textFile) as f:
            for line in f:
                self.filenames.append(line)
            f.close()

    def removeNewlineCharacter(self): #removes newline character from a list of filenames
        self.filenames = [filename.replace('\n','') for filename in self.filenames]
        return(self.filenames)

    def filterFilenames(self,utility,target,fieldname): #keeps subset of list of filenames if textToMatch appears in filename
        filterCriteria = utility + '-' + target + '-' + fieldname
        self.filenames=[file for file in self.filenames if filterCriteria in file]
        return(self.filenames)

master = MasterCsv()
master.removeNewlineCharacter()
master.filterFilenames('sce','Serviceaccount','state')





for i in master.filenames:
    print(i)

#utility, target, fieldname



#print(x)


#filenames = getFilenames()
#cleanFilenames = removeNewlineCharacter(filenames)
#filteredFilenames = filterFilenames(cleanFilenames,'sce')

#print(filteredFilenames)

