import numpy as np
import json
from config import *
import sqlite3
from statistics import median
from build_school_dict import build_school_class

class data_processing(build_school_class):
    def __init__(self, db_fname, pub_fname):
        self.conn = sqlite3.connect(db_fname)
        self.cur = self.conn.cursor()
        self.load_author()
        self.load_publication(pub_fname)
        self.conn.close()

    def load_publication(self, pub_fname):
        """read publication information"""
        with open(pub_fname, 'r') as jf:
            bdata_ = json.load(jf)
        self.bdata = {}
        for k in bdata_.keys():
            self.bdata[k] = bdata_[k]
            bdata_[k] = None
        bdata_ = None


    def save_data(self, sn_list, data, fname):
        with open("result/" + fname + ".txt","a+",encoding = 'utf-8-sig') as output_file:
            output_file.write('{:<80}  {:<5} '.format("School Name", fname) + "\n")
            for i in range(len(sn_list)):
                output_file.write('{:<80}  {:<5} '.format(sn_list[i], data[i]) + "\n")

    def cal_faculty_number(self, save = False):
        '''Calcualte number of faculty in each department. 
        If "save" is True,  save to Faculty_number.txt file'''
        fnum = []
        sn_list = []
        for sn in self.author_dict.keys():
            sn_list.append(sn)
            fnum.append(len(self.author_dict[sn].keys()))
        if save:
            self.save_data(sn_list, fnum, "Faculty_number")
    

    def calc_medi_hindex(self, save = False):
        '''Calcualte median index of each department. 
        If "save" is True,  save to Median_hindex.txt file'''
        medi_hindex = []
        sn_list = []
        for sn in self.author_dict.keys():
            sn_list.append(sn)
            medi_hindex.append(median([self.author_dict[sn][x]["hindex"] for x in self.author_dict[sn].keys()]))
        if save:
            self.save_data(sn_list, medi_hindex, "Median_hindex")
    
    def calc_medi_citation(self, save = False):
        '''Calcualte median citation of each department. If "save" is True,  save to Median_citation.txt file'''
        medi_cit = []
        sn_list = []
        for sn in self.author_dict.keys():
            sn_list.append(sn)
            medi_cit.append(median([self.author_dict[sn][x]["ncitation"] for x in self.author_dict[sn].keys()]))
        if save:
            self.save_data(sn_list, medi_cit, "Median_hindex")

    def calc_medi_publication_all(self, save = False):
        '''Calcualte the median value of publication number of each 
        faculty in his/her whole career. If "save" is True, data save to Median_publication_all.txt file'''
        medi_pub_all = []
        sn_list = []
        for sn in self.author_dict.keys():
            sn_list.append(sn)
            medi_pub_all.append(median([self.author_dict[sn][x]["npapers"] for x in self.author_dict[sn].keys()]))
        if save:
            self.save_data(sn_list, medi_pub_all, "Median_publication_all")

    def calc_medi_publication_part(self, start = 1900, end = 2019, save = False):
        '''Calcualte the median value of publication number of each 
        faculty within certain time interval. If 'save' is ture, data is saved to Median_publication_from_"start"_to_"end".txt file
        default time range is from 1900 to 2019'''
        medi_pub_part = []
        sn_list = []
        for i in self.bdata.keys():
            sn_list.append(self.bdata[i][0][0]["affil"])
            pub_list = []
            for author in self.bdata[i]:
                num_of_pub = 0
                for publication in author:
                    if publication["year"]:
                        if start <= int(publication["year"]) <= end:
                            num_of_pub += 1
                pub_list.append(num_of_pub)
            medi_pub_part.append(median(pub_list))
        if save:
            self.save_data(sn_list, medi_pub_part, "Median_publication_from_" + str(start) + "_to_" + str(end))

    def calc_medi_high_impact_journals(self, start = 1900, end = 2019, save = False):
        '''Calcualte the number of papers published on high impact journals (Nature and Nature X, Science, Cell) from each 
        faculty within certain time interval in each department. If 'save' is ture, data is saved to Median_high_impact_journals_from_"start"_to_"end".txt file
        default time range is from 1900 to 2019'''
        medi_num = []
        sn_list = []
        for i in self.bdata.keys():
            sn_list.append(self.bdata[i][0][0]["affil"])
            num_list = []
            for author in self.bdata[i]:
                num_of_pub = 0
                for publication in author:
                    if publication["year"]:
                        if start <= int(publication["year"]) <= end and publication["journalName"]:
                            jname = publication["journalName"].lower()
                            if ("nature" in jname and len(jname) < 45) or jname == "science" or jname == "cell":
                                    num_of_pub += 1
                                    print("Journal name is ", publication["journalName"])
                num_list.append(num_of_pub)
            medi_num.append(median(num_list))
        if save:
            self.save_data(sn_list, medi_num, "Median_high_impact_journals_from_" + str(start) + "_to_" + str(end))




if __name__ == "__main__":
    dp = data_processing(db_fname, pub_fname)
    dp.cal_faculty_number(save = True)