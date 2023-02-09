'''
Created on 9 apr. 2017

@author: GerbenRienk
'''

import hashlib
import zeep 
from lxml import etree
from zeep.wsse import UsernameToken
import requests

class studySubjectWS(object):
    '''
    class for the study subject webservice:
    to retrieve all study events for one Study
    '''

    def __init__(self, username, password, baseUrl):
        passwordHash = hashlib.sha1(password.encode('utf-8')).hexdigest()
        wsUrl = baseUrl + '/ws/study/v1/studySubjectWsdl.wsdl'
        self._client = zeep.Client(
            wsUrl,
            strict=False,
            wsse=UsernameToken(username, password=passwordHash))

    def getStudySubjectEvents(self,studyIdentifier):
        """Get xml output of study subject events

        """
        with self._client.options(raw_response=True):
            response = self._client.service.listAllByStudy({
                'identifier': studyIdentifier
                })
            if response.status_code != 200:
                return None

            #the response needs cleaning up
            document = str(response.content)
            document = document[document.index('<SOAP'):]
            document = document[0:document.index('</SOAP-ENV:Envelope>') + 20]
            
            xml_output = etree.fromstring(document)
            relevant_part = xml_output.xpath('//ns4:studySubjects', namespaces={
                'ns2': 'http://openclinica.org/ws/beans', 'ns4': 'http://openclinica.org/ws/studySubject/v1'
            })
            return relevant_part

    def getListStudySubjectEvents(self,studyIdentifier):
        for all_subjects in self.getStudySubjectEvents(studyIdentifier):    
            #initialise a list to return
            all_studysubject_events = []
            for one_subject in all_subjects.xpath('//ns2:studySubject', namespaces={'ns2': 'http://openclinica.org/ws/beans'}):
                for one_subject_infoblocks in one_subject.getchildren():
                    #is this the label?
                    if one_subject_infoblocks.tag == '{http://openclinica.org/ws/beans}label':
                        studySubjectID = one_subject_infoblocks.text
                    if one_subject_infoblocks.tag == '{http://openclinica.org/ws/beans}events':
                        for all_events in one_subject_infoblocks.getchildren():
                            for one_event_info in all_events.getchildren():
                                if one_event_info.tag == '{http://openclinica.org/ws/beans}eventDefinitionOID':
                                    eventDefinitionOID = one_event_info.text
                                if one_event_info.tag == '{http://openclinica.org/ws/beans}startDate':
                                    startDate = one_event_info.text
                            
                            one_studysubject_event = studySubjectID,eventDefinitionOID,startDate
                            all_studysubject_events.append(one_studysubject_event)
        return all_studysubject_events


class dataWS(object):
    '''
    class for the study subject webservice:
    to import data
    '''
    def __init__(self, username, password, baseUrl):
        self._passwordHash = hashlib.sha1(password.encode('utf-8')).hexdigest()
        self._wsUrl = baseUrl + '/ws/data/v1/dataWsdl.wsdl'
        self._username = username
        
    def importData(self,odm_data):
        
        _dataWsUrl = self._wsUrl
        
        headers = {'content-type': 'text/xml'}
        body = ''
        body = body + '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v1="http://openclinica.org/ws/data/v1" xmlns:bean="http://openclinica.org/ws/beans">'
        body = body + '  <soapenv:Header>'
        body = body + '    <wsse:Security soapenv:mustUnderstand="1" xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">'
        body = body + '      <wsse:UsernameToken wsu:Id="UsernameToken-27777511" xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">'
        body = body + '        <wsse:Username>' + self._username + '</wsse:Username>'
        body = body + '        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">' + self._passwordHash + '</wsse:Password>'
        body = body + '      </wsse:UsernameToken>'
        body = body + '    </wsse:Security>'
        body = body + '  </soapenv:Header>'
        body = body + '  <soapenv:Body>'
        body = body + '    <v1:importRequest>'
        body = body + odm_data
        body = body + '    </v1:importRequest>'
        body = body + '  </soapenv:Body>'
        body = body + '</soapenv:Envelope>'
        
        xml_as_string = requests.post(_dataWsUrl,data=body,headers=headers).content.decode('utf-8')
        #print('what we got from the web service')
        #print(odm_data)
        #print(xml_as_string)
        tree = etree.fromstring(xml_as_string)
        results = ''
        for result_tag in tree.findall('.//{http://openclinica.org/ws/data/v1}result'):
            results = results + result_tag.text
            if (result_tag.text == 'Fail'):
                for result_tag in tree.findall('.//{http://openclinica.org/ws/data/v1}error'):
                    results = results + ': ' + result_tag.text
                
        #print(results)
        return results
    
if __name__ == "__main__":
    pass 