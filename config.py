import os
import platform 



###########################
#Initial Input
"""Faculty list is used as initial input for the whole program.
This list is generated manually to make sure its accuracy. University
names and faculty names must be close to the names stored in the Scopus
database"""
faculty_list = "data/faculty_list.txt"
num_of_school = 101 #number of shool that will be analyzed. Up to 101.

###########################
#Saved database
"""Results searched on Scopus will be save locally. University information
(University name and its scopus ID), faculty informtion (name, personal scopus id,
affiliation name and id, number of publication/citaion, H-index) and search status 
(success or false) will be save at chemrank.db. Publication information (author, 
journal name, affiliation, year) will be save at publication.json"""
db_fname =  'data/chemrank.db'
pub_fname = 'data/publication.json'




###########################
#Data processing configuration
save_result = True   
start_time = 2000   #starting year for "calc_medi_publication_part" and "calc_medi_high_impact_journals", default value is 2000
end_time = 2019     #ending year for "calc_medi_publication_part" and "calc_medi_high_impact_journals", default value is 2019


###########################
"""Scopus API seaching key, users should apply on Scopus API website and 
copy to here more detail can be found in https://dev.elsevier.com/"""
apikey = "*********************"



