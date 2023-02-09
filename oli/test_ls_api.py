'''
Created January 2023
This file is meant to test just the init of the connection with the LimeSurvey API
@author: GerbenRienk
'''

from utils.dictfile import readDictFile
from utils.limesurveyrc2api import LimeSurveyRemoteControl2API

def test_api():
    # read configuration file for usernames and passwords and other parameters
    config=readDictFile('oli.config')
    # set from this config the sid, because it used everywhere
    api=LimeSurveyRemoteControl2API(config)
    print(api.sessionkey)
    
if __name__ == '__main__':
    test_api()
