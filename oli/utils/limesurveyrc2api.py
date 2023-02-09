import requests
import json
from collections import OrderedDict

class LimeSurveyRemoteControl2API(object):
    def __init__(self, config):
        '''
        Takes a config-dictionary as parameter. To create an object of this class 
        the dictionary should at least have Values for Keys api_url, client_id and client_secret
        '''
        # default to zero length strings
        self.url = 'https://api_url.in.config'
        self.ls_user = ''
        self.ls_password = ''
        
        try:
            self.url = config['lsUrl']
            self.ls_user = config['lsUser']
            self.ls_password = config['lsPassword']
        except Exception as _error:
            print(_error)
            
        #self.url = url
        self.headers = {"content-type": "application/json", "connection": "Keep-Alive"}
        self.utils = _Utils(self)
        self.sessions = _Sessions(self)
        self.surveys = _Surveys(self)
        self.tokens = _Tokens(self)
        self.questions = _Questions(self)
        self.responses = _Responses(self)
        
        #now try to get a sessionkey with these values
        self.sessionkey=self.sessions.get_session_key(self.ls_user, self.ls_password)


class _Utils(object):

    def __init__(self, lime_survey_api):
        self.api = lime_survey_api
    
    def request(self, data, url=None, headers=None):
        """
        Return the result of an API call, or None.

        Exceptions are logged rather than raised.

        Parameters
        :param data: Method name and parameters to send to the API.
        :type data: String
        :param url: Location of the LimeSurvey API endpoint.
        :type url: String
        :param headers: HTTP headers to add to the request.
        :type headers: Dict

        Return
        :return: Dictionary containing result of API call, or None.
        """
        if url is None:
            url = self.api.url
        if headers is None:
            headers = self.api.headers
        return_value = None
        try:
            response = requests.post(url, headers=headers, data=data)
            if len(response.content) > 0:
                return_value = response.json()
        except requests.ConnectionError as pe:
            # TODO: some handling here, for now just print pe
            print(pe)
            return_value = None
        return return_value

    @staticmethod
    def prepare_params(method, params):
        """
        Prepare remote procedure call parameter dictionary.

        Important! Despite being provided as key-value, the API treats all
        parameters as positional. OrderedDict should be used to ensure this,
        otherwise some calls may randomly fail.

        Parameters
        :param method: Name of API method to call.
        :type method: String
        :param params: Parameters to the specified API call.
        :type params: OrderedDict

        Return
        :return: JSON encoded string with method and parameters.
        """
        data = OrderedDict([
            ('method', method),
            ('params', params),
            ('id', 1)
        ])
        data_json = json.dumps(data)
        return data_json


class _Sessions(object):

    def __init__(self, lime_survey_api):
        self.api = lime_survey_api

    def get_session_key(self, username, password):
        """
        Get a session key for all subsequent API calls.

        Parameters
        :param username: LimeSurvey username to authenticate with.
        :type username: String
        :param password: LimeSurvey password to authenticate with.
        :type password: String
        """
        params = OrderedDict([
            ("username", username),
            ("password", password)
        ])
        data = self.api.utils.prepare_params('get_session_key', params)
        response = self.api.utils.request(data)
        this_session_key = response.get('result')
        return this_session_key

    def release_session_key(self, session_key):
        """
        Close an open session.
        """
        params = {'sSessionKey': session_key}
        data = self.api.utils.prepare_params('release_session_key', params)
        response = self.api.utils.request(data)
        return response


class _Surveys(object):

    def __init__(self, lime_survey_api):
        self.api = lime_survey_api

    def list_surveys(self, session_key, username):
        """
        List surveys accessible to the specified username.

        Parameters
        :param session_key: Active LSRC2 session key
        :type session_key: String
        :param username: LimeSurvey username to list accessible surveys for.
        :type username: String
        """
        params = OrderedDict([
            ('sSessionKey', session_key),
            ('iSurveyID', username)
        ])
        data = self.api.utils.prepare_params('list_surveys', params)
        response = self.api.utils.request(data)
        return response


class _Tokens(object):

    def __init__(self, lime_survey_api):
        self.api = lime_survey_api

    def add_participants(self, session_key, survey_id, participant_data,
                         create_token_key=True):
        """
        Add participants to the specified survey.

        Parameters
        :param session_key: Active LSRC2 session key
        :type session_key: String
        :param survey_id: ID of survey to delete participants from.
        :type survey_id: Integer
        :param participant_data: List of participant detail dictionaries.
        :type participant_data: List[Dict]
        """
        params = OrderedDict([
            ('sSessionKey', session_key),
            ('iSurveyID', survey_id),
            ('participantData', participant_data),
            ('bCreateToken', create_token_key)
        ])
        data = self.api.utils.prepare_params('add_participants', params)
        partbit = json.dumps(participant_data)
        data = data.replace(partbit, '['+partbit+']')
        response = self.api.utils.request(data)
        return response

    def list_participants(self, survey_id, start=0, limit=10000, verbose=False):
        """
        List participants of the specified survey.
        * @access public
        * @param string $sSessionKey Auth credentials
        * @param int $iSurveyID Id of the survey to list participants
        * @param int $iStart Start id of the token list
        * @param int $iLimit Number of participants to return
        * @param bool $bUnused If you want unused tokens, set true
        * @param bool|array $aAttributes The extented attributes that we want
        * @param array $aConditions Optional conditions to limit the list, e.g. with array('email' => 'info@example.com')
        * @return array The list of tokens
        Parameters
        :param session_key: Active LSRC2 session key
        :type session_key: String
        :param survey_id: ID of survey to list participants from.
        :type survey_id: Integer
        """
        params = OrderedDict([
            ('sSessionKey', self.api.sessionkey),
            ('iSurveyID', survey_id),
            ('iStart', start),
            ('iLimit', limit),
            ('bUnused', False),
            ('aAttributes', ('attributes_bit'))
        ])
        # transform into json-format
        data = self.api.utils.prepare_params('list_participants', params)
        if verbose == True:
            print(data)
        # but the attributes bit is not well formed, so we manually correct that
        data = data.replace('"attributes_bit"', '["completed"]')
        response = self.api.utils.request(data)
        if verbose == True:
            print(response)
        return response

    def delete_participants(self, session_key, survey_id, tokens):
        """
        Delete participants (by token) from the specified survey.

        Parameters
        :param session_key: Active LSRC2 session key
        :type session_key: String
        :param survey_id: ID of survey to delete participants from.
        :type survey_id: Integer
        :param tokens: List of token IDs for participants to delete.
        :type tokens: List[Integer]
        """
        params = OrderedDict([
            ('sSessionKey', session_key),
            ('iSurveyID', survey_id),
            ('aTokenIDs', tokens)
        ])
        data = self.api.utils.prepare_params('delete_participants', params)
        response = self.api.utils.request(data)
        return response
    
    def get_response_ids(self, survey_id, token, verbose=True):
        params = OrderedDict([
            ('sSessionKey', self.api.sessionkey),
            ('iSurveyID', survey_id),
            ('sToken', token)
        ])
        data = self.api.utils.prepare_params('get_response_ids', params)
        if verbose == True:
            print(data)
        response = self.api.utils.request(data)
        return response
        

    def export_response_by_token(self, survey_id, token, verbose=True):
        """
        $sSessionKey string
        $iSurveyID integer
        $sDocumentType string pdf, csv, xls, doc, json
        $sToken string
        $sLanguageCode string
        $sCompletionStatus string Optional 'complete','incomplete' or 'all' - defaults to 'all'
        $sHeadingType string 'code','full' or 'abbreviated' Optional defaults to 'code'
        $sResponseType string 'short' or 'long' Optional defaults to 'short'
        $aFields array Optional Selected fields   
        
        "params": { "sSessionKey": "%s",
                                    "iSurveyID":  %s,
                                    "sDocumentType": "json",
                                    "sToken":  "%s",
                                    "$sLanguageCode": "%s",
                                    "sCompletationStatus": "all",
                                    "sHeadingType": "code",
                                    "sResponseType": "long"
        """
        #$sSessionKey, $iSurveyID, 'json', $sToken, null, 'all', 'code', 'long')
        params = OrderedDict([
            ('sSessionKey', self.api.sessionkey),
            ('iSurveyID', survey_id),
            ('sDocumentType', 'json'),
            ('sToken', token),
            ('sLanguageCode', 'en'),
            ('sCompletationStatus', 'all'),
            ('sHeadingType', 'code'),
            ('sResponseType', 'short')
        ])
        data = self.api.utils.prepare_params('export_responses_by_token', params)
        if verbose == True:
            print(data)
        response = self.api.utils.request(data)
        return response
    
class _Questions(object):

    def __init__(self, lime_survey_api):
        self.api = lime_survey_api

    def list_questions(self, session_key, survey_id,
                       group_id=None, language=None):
        """
        Return a list of questions from the specified survey.

        Parameters
        :param session_key: Active LSRC2 session key
        :type session_key: String
        :param survey_id: ID of survey to list questions from.
        :type survey_id: Integer
        :param group_id: ID of the question group to filter on.
        :type group_id: Integer
        :param language: Language of survey to return for.
        :type language: String
        """

        params = OrderedDict([
            ('sSessionKey', session_key),
            ('iSurveyID', survey_id),
            ('iGroupID', group_id),
            ('sLanguage', language)
        ])
        data = self.api.utils.prepare_params('list_questions', params)
        response = self.api.utils.request(data)
        return response
 
class _Responses(object):

    def __init__(self, lime_survey_api):
        self.api = lime_survey_api

    def export_responses(self, survey_id,
                       document_type='json', language='en'):
        """
        Return a list of questions from the specified survey.

        Parameters
        :param session_key: Active LSRC2 session key
        :type session_key: String
        :param survey_id: ID of survey to list questions from.
        :type survey_id: Integer
        :param document_type: pdf,csv,xls,doc,json.
        :type document_type: String
        :param language: Language of survey to return for.
        :type language: String
        """

        params = OrderedDict([
            ('sSessionKey', self.api.sessionkey),
            ('iSurveyID', survey_id),
            ('sDocumentType', document_type),
            ('sLanguage', language)
        ])
        data = self.api.utils.prepare_params('export_responses', params)
        response = self.api.utils.request(data)
        return response   
"""
from the online documentation:
export_responses
/**
* RPC Routine to export responses.
* Returns the requested file as base64 encoded string
*
* @access public
* @param string $sSessionKey Auth credentials
* @param int $iSurveyID Id of the Survey
* @param string $sDocumentType pdf,csv,xls,doc,json
* @param string $sLanguageCode The language to be used
* @param string $sCompletionStatus Optional 'complete','incomplete' or 'all' - defaults to 'all'
* @param string $sHeadingType 'code','full' or 'abbreviated' Optional defaults to 'code'
* @param string $sResponseType 'short' or 'long' Optional defaults to 'short'
* @param integer $iFromResponseID Optional
* @param integer $iToResponseID Optional
* @param array $aFields Optional Selected fields
* @return array|string On success: Requested file as base 64-encoded string. On failure array with error information
* */
"""