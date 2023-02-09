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
    # initiate the api for communication with limesurvey
    api=LimeSurveyRemoteControl2API(config)
    
    # request all tokens
    all_tokens=api.tokens.list_participants(sid, start=0, limit=1100, verbose=False)
    total_processed = 0
    for one_token in all_tokens['result']:
        if not one_token['completed'] == 'N':
            this_token=one_token['token']
            this_child_code=one_token['participant_info']['firstname']
            # now request the encoded response, associated with this token
            response_encoded=api.tokens.export_response_by_token(sid, this_token, verbose=False)
            # decode the response
            response_decoded=base64.b64decode(response_encoded['result'])
            # make the response a dictionary, with one entry
            responses_dict = json.loads(response_decoded)
            one_response=responses_dict['responses'][0]
            print(this_child_code, one_response)
            total_processed = total_processed + 1
    
    print('total %s' % total_processed)
    
if __name__ == '__main__':
    test_tokens()
