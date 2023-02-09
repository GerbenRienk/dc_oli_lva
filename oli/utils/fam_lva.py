

def write_odm_line( oc_item_name, ls_item_value, is_date=False, is_time=False, is_decimal=False, is_integer=False, is_utf8 = False):
    _one_line = ''
    if (ls_item_value):
        _this_value = ls_item_value
        if (is_date):
            _this_value = ls_item_value[0:10]
        if (is_time):
            # time field: for now we do nothing with it
            _this_value = _this_value           
        if (is_decimal):
            try:
                float(ls_item_value)
                _this_value = str(ls_item_value)
            except:
                _this_value = 'CONVERSION-ERROR %s value %s to float' % (oc_item_name, ls_item_value)
        if (is_integer):
            try:
                int(ls_item_value)
                _this_value = str(ls_item_value)
            except:
                _this_value = 'CONVERSION-ERROR %s value %s to integer' % (oc_item_name, ls_item_value)
        if (is_utf8):
            _this_value = str(_this_value.encode(encoding="ascii",errors="xmlcharrefreplace"))
            # now we have something like b'some text &amp; more' so we want to loose the first two characters and the last one
            # TODO: make this nicer somehow
            _this_value = _this_value[2:]
            _this_value = _this_value[:-1]
            # and finally, replace double quotes with &quot;
            _this_value = _this_value.replace('"', '&quot;')  
                 
        _one_line = _one_line + '            <ItemData ItemOID="' + oc_item_name + '" Value="' + _this_value + '"/>'
    else:
        _one_line = _one_line + '            <ItemData ItemOID="' + oc_item_name + '" Value=""/>'
    #print(_one_line)
    return _one_line

def compose_odm(study_subject_oid, data_ls, verbose=False):
    """
    compose the xml-content to send to the web-service 
    just for this one occasion we write out everything literally
    and we make a big exception for birth-weight, which is given 
    in grams, but must be imported in kilo's and grams 
    """
    if verbose:
        print('in compose_odm ', study_subject_oid)
        print(data_ls)
        
    if (data_ls['q5birthweightgram'] is not None):
        kilograms = int(float(data_ls['q5birthweightgram'])/1000)
        if(kilograms == 0):
            I_LVFAM_BIRTHWEIGHTKG = ''
        else:
            I_LVFAM_BIRTHWEIGHTKG = str(kilograms)
        grams = int(float(data_ls['q5birthweightgram']) - kilograms * 1000)
        I_LVFAM_BIRTHWEIGHTGR = str(grams)
        #print(data_ls['q5birthweightgram'], I_LVFAM_BIRTHWEIGHTKG, I_LVFAM_BIRTHWEIGHTGR)
    else:
        I_LVFAM_BIRTHWEIGHTKG = ''
        I_LVFAM_BIRTHWEIGHTGR = ''
    
    # opening tags
    _odm_data = ''
    _odm_data = _odm_data + '<ODM>'
    _odm_data = _odm_data + '  <ClinicalData StudyOID="S_CPLVA">'
    _odm_data = _odm_data + '    <SubjectData SubjectKey="' + study_subject_oid + '">'
    _odm_data = _odm_data + '      <StudyEventData StudyEventOID="SE_LVA_CP">'
    _odm_data = _odm_data + '        <FormData FormOID="F_LVFAMILYFORM_V10">'
    _odm_data = _odm_data + '          <ItemGroupData ItemGroupOID="IG_LVFAM_UNGROUPED" ItemGroupRepeatKey="1" TransactionType="Insert">'
    # data section 1
    _odm_data = _odm_data + write_odm_line('I_LVFAM_RELATIONSHIP', data_ls['q1relationship'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_RELATIONSHIPOTH', data_ls['q1relationshipother'], is_utf8 = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_DATEOFBIRTHCOMPLETE', data_ls['q3birthdatecomplete'], is_date=True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_GENDER', data_ls['q4sex'])
    
    # begin first exception !
    _odm_data = _odm_data + write_odm_line('I_LVFAM_BIRTHWEIGHTKG', I_LVFAM_BIRTHWEIGHTKG)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_BIRTHWEIGHTGR', I_LVFAM_BIRTHWEIGHTGR)
    # end first exception

    _odm_data = _odm_data + write_odm_line('I_LVFAM_BREASTFEDEVER', data_ls['q7breastfed'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_BREASTFEDHOWLONG', data_ls['q7breastfedmonths'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_BREASTEXCLEVER', data_ls['q8breastfedexclusive'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_BREASTEXCLUSIVE', data_ls['q8breastexclusive'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_FORMULAMILK', data_ls['q08cformulamilk'], is_integer = True)
    
    # another hack: option 8 is in limesurvey, but not in libreclinica, so we change that to 7
    if (data_ls['q08dformulamilkstart'] is not None):
        if(data_ls['q08dformulamilkstart'] == '8'):
            I_LVFAM_FORMULAMILSTART = '7'
        else:
            I_LVFAM_FORMULAMILSTART = str(data_ls['q08dformulamilkstart'])
    else:
        I_LVFAM_FORMULAMILSTART = ''
    #_odm_data = _odm_data + write_odm_line('I_LVFAM_FORMULAMILSTART', data_ls['q08dformulamilkstart'], is_integer = True) 
    _odm_data = _odm_data + write_odm_line('I_LVFAM_FORMULAMILSTART', I_LVFAM_FORMULAMILSTART)
    
    _odm_data = _odm_data + write_odm_line('I_LVFAM_COMPLFEEDINGSTART', data_ls['q08dcomplementaryfee'], is_integer = True)

    # data section 2
    _odm_data = _odm_data + write_odm_line('I_LVFAM_DISTANCESCHOOLHOME', data_ls['fq09distance'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_TRANSPSCHOOLTO', data_ls['q10transpschoolto'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_TRANSPSCHOOLFROM', data_ls['q10transpschoolfrom'])
    
    q10areasonmotorized = ''
    if (data_ls['fq10areasonmotor[1]'] == 'Y'):
        q10areasonmotorized = q10areasonmotorized + '1,'
    if (data_ls['fq10areasonmotor[2]'] == 'Y'):
        q10areasonmotorized = q10areasonmotorized + '2,'
    if (data_ls['fq10areasonmotor[3]'] == 'Y'):
        q10areasonmotorized = q10areasonmotorized + '3,'
    if (data_ls['fq10areasonmotor[4]'] == 'Y'):
        q10areasonmotorized = q10areasonmotorized + '4,'
    if (data_ls['fq10areasonmotor[5]'] == 'Y'):
        q10areasonmotorized = q10areasonmotorized + '5,'
    if (q10areasonmotorized != '' and q10areasonmotorized[-1] ==','):
        q10areasonmotorized = q10areasonmotorized[0: (len(q10areasonmotorized) -1)]
    _odm_data = _odm_data + write_odm_line('I_LVFAM_REASONMOTORIZED', q10areasonmotorized) 
    _odm_data = _odm_data + write_odm_line('I_LVFAM_REASONMOTORIZEDOTH', data_ls['fq10areasonmotoroth'], is_utf8 = True)

    _odm_data = _odm_data + write_odm_line('I_LVFAM_SAFEROUTESCHOOL', data_ls['q11routesafe'])
    
    _odm_data = _odm_data + write_odm_line('I_LVFAM_LTV_SPORTDANCE', data_ls['fq13sportsdancelv'])
    
    _odm_data = _odm_data + write_odm_line('I_LVFAM_SPORTCLUBFREQHRS', data_ls['q13sportclubshrs'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_SPORTCLUBFREQMIN', data_ls['q13sportclubsmin'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_BEDTIME', data_ls['q14bedtime'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WAKEUPTIME', data_ls['q15wakeuptime'])

    _odm_data = _odm_data + write_odm_line('I_LVFAM_WDSPLAYINGACTIVEH', data_ls['q16playoutwkdayshrs'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WDSPLAYINGACTIVEM', data_ls['q16playoutwkdaysmins'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WEPLAYINGACTIVEH', data_ls['q16playoutwkendshrs'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WEPLAYINGACTIVEM', data_ls['q17playoutwkendsmins'], is_integer = True)

    _odm_data = _odm_data + write_odm_line('I_LVFAM_WDELECTRONICSH', data_ls['q18wdelectronicsh'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WDELECTRONICSM', data_ls['q18wdelectronicsm'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WEELECTRONICSH', data_ls['q18weelectronicsh'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WEELECTRONICSM', data_ls['q18weelectronicsm'], is_integer = True)

    _odm_data = _odm_data + write_odm_line('I_LVFAM_LTV_WDREADING', data_ls['q17readingwkdayslv']) 
    _odm_data = _odm_data + write_odm_line('I_LVFAM_LTV_WEREADING', data_ls['q17readingwkendlv'])
    
    # data section 3
    _odm_data = _odm_data + write_odm_line('I_LVFAM_BREAKFAST', data_ls['q19breakfast'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_FREQFRUIT', data_ls['q20[FreshFruit]'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_FREQVEGETABLES', data_ls['q20[Vegetables]'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_FREQSOFTDRINKS', data_ls['q20[SoftDrinksSugar]'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_FREQCANDY', data_ls['q20[Candy]'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_WEIGHTOPINION', data_ls['q21weightopinion'])

    # data section 4
    _odm_data = _odm_data + write_odm_line('I_LVFAM_SPOUSEAGE', data_ls['q25spousesage'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_SPOUSEHEIGHT', data_ls['q25spouseheight'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_SPOUSEWEIGHT', data_ls['q25spouseweight'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_YOUAGE', data_ls['q25youage'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_YOUHEIGHT', data_ls['q25youheight'], is_decimal = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_YOUWEIGHT', data_ls['q25youweight'], is_decimal = True)

    q26hmnr = ''
    if (data_ls['q26hmnr[1]'] == 'Y'):
        q26hmnr = q26hmnr + '1,'
    if (data_ls['q26hmnr[2]'] == 'Y'):
        q26hmnr = q26hmnr + '2,'
    if (data_ls['q26hmnr[3]'] == 'Y'):
        q26hmnr = q26hmnr + '3,'
    if (data_ls['q26hmnr[4]'] == 'Y'):
        q26hmnr = q26hmnr + '4,'
    if (data_ls['q26hmnr[5]'] == 'Y'):
        q26hmnr = q26hmnr + '5,'
    if (data_ls['q26hmnr[6]'] == 'Y'):
        q26hmnr = q26hmnr + '6,'
    if (data_ls['q26hmnr[7]'] == 'Y'):
        q26hmnr = q26hmnr + '7,'
    if (data_ls['q26hmnr[8]'] == 'Y'):
        q26hmnr = q26hmnr + '8,'
    if (q26hmnr != '' and q26hmnr[-1] ==','):
        q26hmnr = q26hmnr[0: (len(q26hmnr) -1)]
    _odm_data = _odm_data + write_odm_line('I_LVFAM_HOMEADULTS', q26hmnr)

    _odm_data = _odm_data + write_odm_line('I_LVFAM_HOMEADULTSSPEC', data_ls['q26hmnrelsespec'], is_utf8 = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_HMNRBROTHER', data_ls['q26homebrother'], is_integer = True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_HMNRSISTER', data_ls['q26homesister'], is_integer = True)

    _odm_data = _odm_data + write_odm_line('I_LVFAM_EDUYOU', data_ls['q31eduyou'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_EDUSPOUSE', data_ls['q31eduspouse'])
    _odm_data = _odm_data + write_odm_line('I_LVFAM_EARNINGS', data_ls['q32earnings'])
    
    _odm_data = _odm_data + write_odm_line('I_LVFAM_DATECOMPLETION', data_ls['submitdate'], is_date=True)
    _odm_data = _odm_data + write_odm_line('I_LVFAM_REMARKS', data_ls['q35remarks'], is_utf8 = True)
    
    # closing tags
    _odm_data = _odm_data + '          </ItemGroupData>'
    _odm_data = _odm_data + '        </FormData>'
    _odm_data = _odm_data + '      </StudyEventData>'
    _odm_data = _odm_data + '    </SubjectData>'
    _odm_data = _odm_data + '  </ClinicalData>'
    _odm_data = _odm_data + '</ODM>'

    return _odm_data
