'''
Created February 2023

@author: Gerben Rienk
'''
import time
import datetime
import json
import base64
from utils.logmailer import MailThisLogFile
from utils.dictfile import readDictFile
from utils.fam_lva import compose_odm
from utils.limesurveyrc2api import LimeSurveyRemoteControl2API
from utils.ocwebservices import dataWS
from utils.pg_api import ConnToOliDB, PGSubject
from utils.reporter import Reporter

def cycle_through_syncs():
    my_report = Reporter()
    
    start_time = datetime.datetime.now()
    my_report.append_to_report('INFO: cycle started at ' + str(start_time))
    # read configuration file for user-names and passwords and other parameters
    config=readDictFile('oli.config')
    # set from this config the sid, because it used everywhere
    sid = int(config['sid'])
    # initialise the api for communication with limesurvey
    api=LimeSurveyRemoteControl2API(config)
    
    # create a connection to the postgresql database
    conn = ConnToOliDB()
    my_report.append_to_report(conn.init_result)

    # initialise the lc-webservice
    myDataWS = dataWS(config['userName'], config['password'], config['baseUrl'])
    
    #start the cycling here
    while True:
        # request all tokens
        all_tokens=api.tokens.list_participants(sid, start=0, limit=12000, verbose=False)
        for one_token in all_tokens['result']:
            if not one_token['completed'] == 'N':
                this_token=one_token['token']
                study_subject_id=one_token['participant_info']['firstname']
                # now request the encoded response, associated with this token
                response_encoded=api.tokens.export_response_by_token(sid, this_token, verbose=False)
                # decode the response
                response_decoded=base64.b64decode(response_encoded['result'])
                # make the response a dictionary, with one entry
                responses_dict = json.loads(response_decoded)
                one_response_data=responses_dict['responses'][0]
                # get the id of this response, so we can use it in our administration
                response_id=int(one_response_data['id'])
                # check if this combination sid-response-id already exists and if not, add it
                conn.TryToAddSubjectToDB(sid, response_id)
                #print(study_subject_id, one_response_data)
                if (len(study_subject_id) != 13):
                    # write this to error report 
                    my_report.append_to_report('ERROR: Incorrect study subject id for response id %i: %s' % (response_id, study_subject_id))
                else:
                    # write the child-code / study subject id to the database
                    if (conn.DLookup('study_subject_id', 'ls_responses', 'sid=%i and response_id=%i' % (sid, response_id)) is None):
                        conn.WriteStudySubjectID(sid, response_id, study_subject_id)

                    # check if we already have a valid study subject oid
                    study_subject_oid = conn.DLookup('study_subject_oid', 'ls_responses', 'sid=%i and response_id=%i' % (sid, response_id))                    
                    if (study_subject_oid is None or study_subject_oid == ''):
                        # try to get a valid study subject oid
                        study_subject_oid = PGSubject(study_subject_id).GetSSOID(verbose=False)
                        # we don't know if we now have study_subject_oid,
                        # but the procedure only writes the study subject oid to the database for later use
                        # if it is not null
                        conn.WriteStudySubjectOID(sid, response_id, study_subject_oid, verbose=False)
                
                # only continue if we have both study subject id and study subject oid
                if (study_subject_oid is None):
                    # write this to error report
                    my_report.append_to_report('ERROR: Missing OID for ChildCode %s' % study_subject_id)
                else:
                    # only compose the odm and try to import the result
                    # if this wasn't done before, so look at date_completed
                    if(conn.DLookup('date_completed', 'ls_responses', 'sid=%i and response_id=%i' % (sid, response_id)) is None):
                        ws_request = compose_odm(study_subject_oid, one_response_data, verbose=False)
                        conn.WriteDataWSRequest(sid, response_id, ws_request)
                        import_result = myDataWS.importData(ws_request)
                        conn.WriteDataWSResponse(sid, response_id, import_result)
                        if (import_result.find('Success') == 0):
                            my_report.append_to_report('INFO: Successfully imported data for %s (%s)' % (study_subject_id, study_subject_oid))
                            conn.SetResponseComplete(sid, response_id)
                        else:
                            item_starts_at = import_result.find('I_')
                            if (item_starts_at == -1):
                                my_report.append_to_report('ERROR: import for %s failed with message "%s"' % (study_subject_id, import_result))
                            else:
                                import_result=import_result.encode("utf-8")
                                my_report.append_to_report('ERROR: import for %s failed with message "%s" and more' % (study_subject_id, import_result[item_starts_at:]))

        # check if we must continue looping, or break the loop
        # first sleep a bit, so we do not eat up all CPU
        time.sleep(int(config['sleep_this_long']))
        current_time = datetime.datetime.now()
        difference = current_time - start_time
        loop_this_long = config['loop_this_long']
        max_diff_list = loop_this_long.split(sep=':') 
        max_difference = datetime.timedelta(hours=int(max_diff_list[0]), minutes=int(max_diff_list[1]), seconds=int(max_diff_list[2]))
        if difference > max_difference:
            break
     
    my_report.append_to_report('INFO: finished looping from %s till %s.' % (start_time, current_time))
    # close the file so we can send it
    my_report.close_file()
    MailThisLogFile('logs/report.txt')
            
if __name__ == '__main__':
    cycle_through_syncs()
