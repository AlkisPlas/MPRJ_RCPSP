#!/usr/bin/env python
import sys
import os
import re
import json
import csv

def convert_file(filename, writer):
    instname = filename.split('_results')[0]
    with open(dis_dir + filename, 'r') as fpdis:
        data_dis = json.load(fpdis)

        lower_bound = data_dis['Problem'][0]['Lower bound']
        upper_bound = data_dis['Problem'][0]['Upper bound']
        variables = data_dis['Problem'][0]['Number of variables']
        constraints = data_dis['Problem'][0]['Number of constraints']
        time = data_dis['Solver'][0]['User time']

        data1 = [instname, 'discrete', lower_bound, upper_bound, time, variables, constraints]
    
    for filename in os.listdir(con_dir):
        if(filename.startswith(instname)):
            with open(con_dir + filename, 'r') as fpcon:
                data_con = json.load(fpcon)
                lower_bound = data_con['Problem'][0]['Lower bound']
                upper_bound = data_con['Problem'][0]['Upper bound']
                variables = data_con['Problem'][0]['Number of variables']
                constraints = data_con['Problem'][0]['Number of constraints']
                time = data_con['Solver'][0]['User time']

                data = [instname, 'continuous', lower_bound, upper_bound, time, variables, constraints]
                writer.writerow(data1)
                writer.writerow(data)
        

base_dir = sys.argv[1]
instance = sys.argv[2]
dis_dir = base_dir + '/discrete/' + instance + '/'
con_dir = base_dir + '/discrete/' + instance + '/'

f = open(instance + 'results.csv', 'w')

writer = csv.writer(f)
header = ['instance', 'formulation', 'lower_bound', 'upper_bound', 'time', 'variables', 'constaints']
writer.writerow(header)

for filename in os.listdir(dis_dir): 
    if filename.endswith(".json"): 
        try:
            convert_file(filename, writer)
        except:
            pass
      
f.close()