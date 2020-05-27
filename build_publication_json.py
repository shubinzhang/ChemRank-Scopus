import json
import sqlite3
from config import *
from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch
from elsapy.elsprofile import ElsAuthor
from build_school_dict import build_school_class


class build_json_class(build_school_class):
    def __init__(self, apikey, db_fname):
        self.client = ElsClient(apikey)
        self.client.inst_token = None
        self.conn = sqlite3.connect(db_fname)
        self.cur = self.conn.cursor()
        self.load_author()
        self.conn.close()

    
    def author_pubs(self,author_id,sname):
        """
        Obtain publication list for a given Scopus author ID author_id
        client - object of the ElsClient class
        returns publication list and full output of the ElsSearch search request
        """
        doc_srch = ElsSearch('AU-ID(%s)'%author_id,'scopus')
        doc_srch.execute(self.client, get_all = True)
        pubs = []
        
        for rslt in doc_srch.results:
            if 'prism:coverDate' in rslt.keys():
                year = rslt['prism:coverDate'].split('-')[0]
            else:
                year = None
            if 'citedby-count' in rslt.keys():
                citedby = int(rslt['citedby-count'])
            else:
                citedby = None
            if "dc:identifier" in rslt.keys():
                pub_scopusid = rslt['dc:identifier'].split(':')[1]
            else:
                pub_scopusid = None
            if 'prism:publicationName' in rslt.keys():
                jrnlname = rslt['prism:publicationName']
            else:
                jrnlname = None
            author_pub_dict = {"affil":sname, "cit":citedby, "id":pub_scopusid, "journalName":jrnlname, "scopusid":author_id,"year":year }
            pubs.append(author_pub_dict)
        
        return pubs

    def build_publication_dictionary(self):
        """create json file include publication information of each faculty"""
        for rank, sn in enumerate(self.author_dict.keys()):
                print(sn)
                dumped_dict = {}
                temp_pub_list = []
                temp_people_list = []
                for people in self.author_dict[sn].keys():
                    author_id = self.author_dict[sn][people]["id"]
                    current_affil = sn
                    temp_pub_list = self.author_pubs(author_id, current_affil)
                    print ("number of publication in" ,people, ":" ,len(temp_pub_list))
                    temp_people_list.append(temp_pub_list)
                dumped_dict[rank] = temp_people_list
                with open ("publication.json","a+") as pf:
                    json.dump(dumped_dict,pf,indent=4)
        
if __name__=='__main__':
    bj = build_json_class(apikey,db_fname)
    bj.build_publication_dictionary()
