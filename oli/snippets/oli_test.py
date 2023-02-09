'''
Created on 9 apr. 2017

@author: GerbenRienk
'''
import time
import datetime
from utils.logmailer import MailThisLogFile
from utils.dictfile import readDictFile
from utils.ocwebservices import studySubjectWS, dataWS
from utils.limesurveyrc2api import LimeSurveyRemoteControl2API
from utils.pg_api import ConnToOliDB, PGSubject
from utils.reporter import Reporter
from _operator import itemgetter

def cycle_through_syncs():
    my_report = Reporter()
    start_time = datetime.datetime.now()
    my_report.append_to_report('cycle started at ' + str(start_time))
    # read configuration file for usernames and passwords and other parameters
    config=readDictFile('oli.config')
    # read with combinations of StudyEventOIDs and LimeSurvey sids
    event_survey_pairs=readDictFile('event_survey_pairs')

    # initialise the oc-webservice
    myWebService = studySubjectWS(config['userName'], config['password'], config['baseUrl'])
    myDataWS = dataWS(config['userName'], config['password'], config['baseUrl'])

    # create a connection to the postgresql database
    conn = ConnToOliDB()
    my_report.append_to_report(conn.init_result)
    
    while True:
        # retrieve all StudySubjectEvents, using the webservice
        allStudySubjectEvents = myWebService.getListStudySubjectEvents(config['studyIdentifier'])
        # now we have the StudySubjectIDs, run them against the postgresql table subjects
        
        # retrieve the subjects, using the connection to the postgresql database
        subjects_in_db = conn.ReadSubjectsFromDB()
        
        for studysubject_event in allStudySubjectEvents:  
            # check if StudySubjectID is already in pg_database
            add_subject_to_db = True
            for subject_in_db in subjects_in_db:  
                # check if we must check this event
                if(studysubject_event[0] == subject_in_db[1]):
                    add_subject_to_db = False
            if (add_subject_to_db):
                myPgSubject = PGSubject(studysubject_event[0])
                conn.AddSubjectsToDB([(myPgSubject.GetSSOID(), studysubject_event[0])])
                my_report.append_to_report('added %s to database' % studysubject_event[0])
        
        # now all StudySubjects in OpenClinica are also in our postgresql-database
        # so we refresh our list 
        subjects_in_db = conn.ReadSubjectsFromDB()
        
        # collecting LimeSurvey data
        # Make a session, which is a bit of overhaed, but the script will be running for hours.
        api = LimeSurveyRemoteControl2API(config['lsUrl'])
        session_req = api.sessions.get_session_key(config['lsUser'], config['lsPassword'])
        session_key = session_req.get('result')
                    
        # initialise a new list for all tokens of all surveys
        # so we can check if a new token must be created
        all_tokens = []
        for event_oid, sid in event_survey_pairs.items():
            participants_req = api.tokens.list_participants(session_key, sid)
            participants = participants_req.get('result')
            for participant in participants:
                #loop through the participants, but only if there are any
                if participant != 'status':
                    p_info = participant.get('participant_info')
                    all_tokens.append( (p_info.get('firstname'), event_oid, sid, participant.get('token'), participant.get('completed')))
                    
        
        for studysubject_event in allStudySubjectEvents:  
            # check if we must check this event
            if studysubject_event[1] in event_survey_pairs:
                # yes, we must check this event 
                blnAddTokens = True
                for one_token in all_tokens:
                    if one_token[0] == studysubject_event[0] and one_token[1] == studysubject_event[1]:
                        # a token exists
                        blnAddTokens = False
        
                if blnAddTokens:
                    #self._logger.debug("add token for " + studysubject_event[0] + ", " + studysubject_event[1])
                    print ("add token for " + studysubject_event[0] + " " + str(event_survey_pairs[studysubject_event[1]]) + ", " + studysubject_event[1])
                    participant_data = {'firstname': studysubject_event[0]}
                    #add_participant_req = 
                    api.tokens.add_participants(session_key, event_survey_pairs[studysubject_event[1]], participant_data)
                    my_report.append_to_report('created token for survey %s for subject %s' % (sid, studysubject_event[0]))
        
        # we may have added tokens, so refresh all_tokens
        # TODO: lets's make this a method
        all_tokens = []
        for event_oid, sid in event_survey_pairs.items():
            participants_req = api.tokens.list_participants(session_key, sid)
            participants = participants_req.get('result')
            for participant in participants:
                #loop through the participants, but only if there are any
                if participant != 'status':
                    p_info = participant.get('participant_info')
                    all_tokens.append( (p_info.get('firstname'), event_oid, sid, participant.get('token'), participant.get('completed')))      

        # now import the LimeSurvey results into OpenClinica 
        # sorted by study subject id
        sorted_tokens = sorted(all_tokens, key=itemgetter(0))
        last_ssid = 'x'
        lime_survey_header = 'ev. token  completed&#10;---------------------------&#10;'
        lime_survey_data_to_import = lime_survey_header
        for token in sorted_tokens:
            survey_friendly_name = conn.DLookup("friendly_name", "ls_sids", "ls_sid=%d" % (int(token[2])))
            if last_ssid != token[0]:
                # new study subject ID, so write the previous one
                ssoid = conn.DLookup("study_subject_oid", "subjects", "study_subject_id='%s'" % (last_ssid))
                # skip the start-value 
                if last_ssid != 'x':
                    ls_data_in_db = conn.DLookup("ls_data", "subjects", "study_subject_oid='%s'" % (ssoid))
                    if lime_survey_data_to_import != ls_data_in_db:
                        myImport = myDataWS.importLSData(ssoid, lime_survey_data_to_import)
                        conn.WriteLSDataToDB(ssoid, lime_survey_data_to_import, myImport)
                        my_report.append_to_report('wrote ls_data for subject %s 1' % (ssoid))
    
                # reset the variables
                last_ssid = token[0]
                lime_survey_data_to_import = lime_survey_header + survey_friendly_name + ' ' + token[3] + ' ' + token[4] + '&#10;'
            else:
                lime_survey_data_to_import = lime_survey_data_to_import + survey_friendly_name + ' ' +  token[3] + ' ' +  token[4] + '&#10;'
        
        # print the last one
        ssoid = conn.DLookup("study_subject_oid", "subjects", "study_subject_id='%s'" % (last_ssid))
        ls_data_in_db = conn.DLookup("ls_data", "subjects", "study_subject_oid='%s'" % (ssoid))
        if lime_survey_data_to_import != ls_data_in_db:
            myImport = myDataWS.importLSData(ssoid, lime_survey_data_to_import)
            conn.WriteLSDataToDB(ssoid,lime_survey_data_to_import, myImport)
            my_report.append_to_report('wrote ls_data for subject %s 2' % (ssoid))
        
        # some book keeping to check if we must continue looping, or break the loop
        # first sleep a bit, so we do not eat up all CPU
        time.sleep(int(config['sleep_this_long']))
        current_time = datetime.datetime.now()
        difference = current_time - start_time
        loop_this_long = config['loop_this_long']
        max_diff_list = loop_this_long.split(sep=':') 
        max_difference = datetime.timedelta(hours=int(max_diff_list[0]), minutes=int(max_diff_list[1]), seconds=int(max_diff_list[2]))
        if difference > max_difference:
            break
    
    my_report.append_to_report('finished looping from %s till %s.' % (start_time, current_time))
    # close the file so we can send it
    my_report.close_file()
    MailThisLogFile('logs/report.txt')
    
    
if __name__ == '__main__':
    cycle_through_syncs()
