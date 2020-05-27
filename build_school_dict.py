from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch
from elsapy.elsprofile import ElsAuthor
from elsapy.elsdoc import AbsDoc
import Levenshtein as pl
import json
import sqlite3
from config import *
import copy
import time 


class build_school_class():
    def __init__(self,apikey, db_fname, faculty_list, num_of_school):
        """load universities' name from faculty list
        Initialize scopus client objective
        Connect to database"""
        self.read_sname(faculty_list, num_of_school)
        self.client = ElsClient(apikey)
        self.client.inst_token = None
        self.conn = sqlite3.connect(db_fname)
        self.cur = self.conn.cursor()

        
    def read_sname(self, faculty_list, num_of_school = 101):
        #### read faculty_list.txt file, generate school name list and faculty dictionary
        self.sname_list = []
        self.school_dict = {}
        lines = []
        start_index = 1    #store start index of faculty in each school
        with open(faculty_list, 'r', encoding = 'cp1252') as fl:
            ##facult_list file is written in windows, encoding type "cp1252" is required
            for readline in fl:
                lines.append(readline)
        for ind,line in enumerate(lines):
            if ind == 0:
                # The first element should be the name of rank 1 school
                self.sname_list.append(line.strip())
                sname = lines[0].rstrip()
            if line == "\n":
                fname = [name.rstrip() for name in lines[start_index:ind]]
                self.sname_list.append(sname)
                self.school_dict[sname] = {"people":fname}
                start_index = ind + 2
                if len(self.sname_list) < num_of_school:
                    sname = lines[ind+1].rstrip()
                else:
                    break


    def affiliation_id_serch(self, schoolname):
        """Search affiliation ID by name
        client - object of the ElsClient class  """
        school_srch = ElsSearch(' AFFIL(%s)'%schoolname,'affiliation')
        school_srch.execute(self.client)
        return school_srch.results

    def build_sname_dict(self):
        print("Building school database and dictonary")
        self.build_db_school()

        for rank, sn in enumerate(self.sname_list):
            self.school_dict[sn]["status"] = "error"   
            self.school_dict[sn]["rank"] = rank + 1
            school_srch_results = self.affiliation_id_serch(sn)
            for ind, sitem in enumerate(school_srch_results):
                if ind == 0:
                    # The first search result is usually the correct result, apply rough match criteria (character difference less than 10), make sure correct country (e.g. northeastern)
                    if pl.distance(sn.strip(),sitem['affiliation-name'].strip()) <= 12 and sitem['country'] == "United States":
                        self.school_dict[sn]["affil_id"] = [sitem['dc:identifier'].split(':')[1]]
                        self.school_dict[sn]["status"] = "success"
                        break
                else:   
                    ##looking through other search result
                    if pl.distance(sn.strip(),sitem['affiliation-name'].strip()) <= 10  and sitem['dc:identifier'].split(':')[1][0] == "6":
                        if "affil_id" in self.school_dict[sn].keys():
                            self.school_dict[sn]["affil_id"].append(sitem['dc:identifier'].split(':')[1])
                        else:
                            self.school_dict[sn]["affil_id"] = [sitem['dc:identifier'].split(':')[1]]
                        self.school_dict[sn]["status"] = "success"
                        break
            if not self.school_dict[sn]["status"] == "success":
                print("can't find ",sn)
                self.school_dict[sn]["affil_id"] = ["000000"]
            self.cur.execute('INSERT INTO schools VALUES (?,?,?,?)',(sn,self.school_dict[sn]["rank"],str(self.school_dict[sn]["affil_id"]),str(self.school_dict[sn]["status"])))
            self.conn.commit()
            print (sn, self.school_dict[sn]["status"])
            print('-'*40)
        
    def build_db_school(self):
        print("create new school database")
        self.cur.execute('CREATE TABLE IF NOT EXISTS {tn}(schoolname text,rank integer,affil_id text, status text)'.format(tn="schools"))


    def search_auth_by_name(self,fstname, lstname, schoolid_complex):
        """Find author's Scopus ID by first, last name and affiliation ID.
        In case of an error, perform search without affiliation ID and return first author in the serach result
        If author can't be found, return empty entry with status = error"""
        #For universities have one affiliation id
        if len(schoolid_complex) == 1:
            schoolid = schoolid_complex
            auth_srch = ElsSearch('AUTHLASTNAME(%s)'%lstname + ' AUTHFIRST(%s)'%fstname + ' AF-ID(%s)'%schoolid,'author')
            auth_srch.execute(self.client)
            authorfound = auth_srch.results[0]
            if 'error' in authorfound.keys():
                status = 'error'
                #execute raw author search without affiliation
                auth_srch = ElsSearch('AUTHLASTNAME(%s)'%lstname + ' AUTHFIRST(%s)'%fstname ,'author')
                auth_srch.execute(self.client)
                authorfound = auth_srch.results[0]
                if 'error' in authorfound.keys():
                    status = 'error'
                    return status, {}
                #in case subject area is empty
                if 'affiliation-current' in authorfound.keys():
                    #check reseach area, make sure author's reasearch include chemistry or biology or chemical engineer or environment
                    if isinstance(authorfound["subject-area"],list):
                        subject_list = [ subject for subject in authorfound["subject-area"]]
                        subject_abbrev_list = [subject_abbrev["@abbrev"] for subject_abbrev in subject_list ]
                    else:
                        subject_abbrev_list = [authorfound["subject-area"]["@abbrev"]]
                    if "CHEM" or "BIOC" or "CENG" or "ENVI" in subject_abbrev_list:    
                        status = 'success'
                    else:
                        status = "wrong area"
                else:
                    print(fstname, lstname, ' --- can not find affiliation-current in keys')
                    status = 'warning'
            else:
                status = 'success'
        #For universities have two affiliation ids
        else:
            schoolid1 = schoolid_complex[0]
            schoolid2 = schoolid_complex[1]
            print (schoolid1,schoolid2)
            auth_srch = ElsSearch('AUTHLASTNAME(%s)'%lstname + ' AUTHFIRST(%s)'%fstname + ' AF-ID(%s)'%schoolid1,'author')
            auth_srch.execute(self.client)
            authorfound = auth_srch.results[0]
            if 'error' in authorfound.keys():
                auth_srch = ElsSearch('AUTHLASTNAME(%s)'%lstname + ' AUTHFIRST(%s)'%fstname + ' AF-ID(%s)'%schoolid2,'author')
                auth_srch.execute(self.client)
                authorfound = auth_srch.results[0]
            if 'error' in authorfound.keys():
                status = 'error'
                auth_srch = ElsSearch('AUTHLASTNAME(%s)'%lstname + ' AUTHFIRST(%s)'%fstname ,'author')
                auth_srch.execute(self.client)
                authorfound = auth_srch.results[0]
                if 'error' in authorfound.keys():
                    status = 'error'
                    return status, {}
                if 'affiliation-current' in authorfound.keys() and authorfound["subject-area"]:
                    if isinstance(authorfound["subject-area"],list):
                        subject_list = [ subject for subject in authorfound["subject-area"]]
                        subject_abbrev_list = [subject_abbrev["@abbrev"] for subject_abbrev in subject_list ]
                    else:
                        subject_abbrev_list = [authorfound["subject-area"]["@abbrev"]]
                    if "CHEM" or "BIOC" or "CENG" or "ENVI" in subject_abbrev_list:    
                        status = 'success'
                    else:
                        status = "wrong area"

                else:
                    print(fstname, lstname, ' --- can not find affiliation-current in keys')
                    status = 'warning'
            else:
                status = 'success'
        return status, authorfound

    def auth_metrics(self,auth_id):
        """Read author metrics for a given Scopus author ID auth_id
        client - object of the ElsClient class 
        reurns status, author data, total number of paers, citations and h-index """
        my_auth = ElsAuthor(uri = 'https://api.elsevier.com/content/author/author_id/'+auth_id) 
        if my_auth.read(self.client):
            status = 'success'
        else:
            status = 'error'
            print ("can't find author information")
            return None, None, None
        my_auth.read_metrics(self.client)
        if my_auth._data==None:
            npapers, ncitation, hindex = None, None, None
            status = 'error'
            print ("can't find publication information")
        else:
            status = 'success'
            npapers = my_auth._data['coredata']['document-count']
            ncitation = my_auth._data['coredata']['citation-count']
            hindex = my_auth._data['h-index']
        return npapers, ncitation, hindex
    
    def build_people_scopus_dict(self):
        self.build_db_people()
        for rank_1, key in enumerate(self.school_dict.keys()):
            print ("####################################")
            print (key)
            snm = False    #school name in missing faculty list
            snf = False      #school name in wrong area list
            firstname =  [name.strip().split()[0] for name in self.school_dict[key]["people"]]
            lastname = [name.strip().split()[-1] for name in self.school_dict[key]["people"]]
            if len(self.school_dict[key]["affil_id"])<14:
                #For author whose affiliation has one scopus id
                print ("one affiliation Id")
                affid = [self.school_dict[key]["affil_id"]]
            else:
                #For author whose affiliation has two scopus ids
                affid_list = self.school_dict[key]["affil_id"].split(",")
                affid = [affid_list[0],affid_list[1]]
            for i in range(len(firstname)):
                status, authorfound = self.search_auth_by_name(firstname[i],lastname[i],affid)
                if "prefered-name" in authorfound.keys():
                    print (status,authorfound["prefered-name"]["given-name"],authorfound["preferred-name"]["surname"])
                    scoups_givenname, scopus_surname = authorfound["prefered-name"]["given-name"],authorfound["preferred-name"]["surname"]
                elif "name-variant" in authorfound.keys():
                    print (status,authorfound["name-variant"][0]["given-name"],authorfound["name-variant"][0]["surname"])
                    scoups_givenname, scopus_surname = authorfound["name-variant"][0]["given-name"],authorfound["name-variant"][0]["surname"]
                elif status == "success":
                    print (status,firstname[i],lastname[i])
                    scoups_givenname, scopus_surname = firstname[i],lastname[i]
                elif status == "wrong area":
                    ###If author name match but research area is incorrect, author name will be saved to faculty_wrong_area.txt
                    print (status,firstname[i],lastname[i])
                    with open("result/faculty_wrong_area.txt","a+",encoding = 'utf-8-sig') as fw:
                        if snf == False:
                            fw.write("\n")
                            fw.write(key + "\n")
                        fw.write(firstname[i]+"\t"+lastname[i]  +"\n")
                        snf = True
                else:
                    ###Save missing author name to missing_faculty.txt
                    print ("can't find",firstname[i],lastname[i])
                    with open("result/missing_faculty.txt","a+",encoding = 'utf-8-sig') as mf:
                        if snm == False:
                            mf.write("\n")
                            mf.write(key + "\n")
                        mf.write(firstname[i]+"\t"+lastname[i]  +"\n")
                        snm = True
                if status == "success":
                    #School rank
                    rank = rank_1+1
                    if 'dc:identifier' in authorfound.keys():
                        authorid = authorfound['dc:identifier'].split(':')[1]
                        npapers, ncitation, hindex = self.auth_metrics(authorid)
                    else:
                        authorid = None
                        print (firstname[i]+"\t"+lastname[i]+"has no scopus id")
                        npapers, ncitation, hindex = None,None,None
                    fullname = firstname[i]+","+lastname[i]
                    firstname_db = firstname[i]
                    lastname_db = lastname[i]
                    affid_db = self.school_dict[key]["affil_id"][0]
                    curr_affil = key
                    self.cur.execute('INSERT INTO people_scopus VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(fullname, \
                    firstname_db, lastname_db, str(authorid), scoups_givenname, scopus_surname, rank, \
                    affid_db, curr_affil,npapers, status, ncitation, hindex))
                    self.conn.commit()

    def build_db_people(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS people_scopus (fullname text, firstname text, lastname text, \
        scopus_id text, scopus_given_name text, scopus_surname text, affil_rank integer, affil_id text, \
        current_affil text, npapers integer, status text, ncitation integer, hindex integer)')

    def load_author(self):
            """Load data base (people_scopus) and create author dictionary"""
            self.author_dict = {}
            self.cur.execute('SELECT DISTINCT "affil_rank" FROM {tn}'.format(tn = 'people_scopus'))
            self.rank_list = self.cur.fetchall()
            for rank in self.rank_list:
                self.cur.execute('SELECT "hindex", "ncitation", "npapers", "current_affil", "scopus_id",\
                    "fullname" FROM {tn} WHERE (status="success" AND affil_rank = {sr})'.format(tn = 'people_scopus', sr = rank[0]))
                all_rows_cur = self.cur.fetchall()
                self.author_dict[all_rows_cur[0][3]] = {}
                for x in all_rows_cur:
                    self.author_dict[x[3]][x[5]] = {"hindex": x[0], "ncitation": x[1], "npapers": x[2], "id": x[4]}


if __name__=='__main__':
    bs = build_school_class(apikey, db_fname, faculty_list, num_of_school)
    #bs.build_sname_dict()
    #bs.build_people_scopus_dict()

