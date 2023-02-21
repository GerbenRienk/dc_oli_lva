'''
Created January 2023
This file is meant to test requesting all tokens of a limesurvey questionnaire
@author: GerbenRienk
'''
import json
import base64
from utils.dictfile import readDictFile
from utils.limesurveyrc2api import LimeSurveyRemoteControl2API

def test_tokens():
    # read configuration file for usernames and passwords and other parameters
    config=readDictFile('oli.config')
    # get the survey id from the config 
    sid = int(config['sid'])
    # set from this config the sid, because it used everywhere
    api=LimeSurveyRemoteControl2API(config)
    responses_encoded=api.responses.export_responses(sid)
    # print(responses_encoded)
    responses_decoded = base64.b64decode(responses_encoded['result'])
    # print(responses_decoded)
    responses_dict = json.loads(responses_decoded)   #this is a dictionary
    print(responses_dict)
    
if __name__ == '__main__':
    test_tokens()
