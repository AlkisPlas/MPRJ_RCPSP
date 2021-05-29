#!/usr/bin/env python
import sys
import os
import re
import json


def extract_val(lines, line_prefix, exception_msg, sep=':'):
    for line in lines:
        if line.strip().startswith(line_prefix):
            return int(re.sub('\D', '', line.split(sep)[1]))
    raise Exception(exception_msg)


def index_of_line_starting_with(prefix, lines):
    ctr = 0
    for line in lines:
        if line.startswith(prefix):
            return ctr
        ctr += 1
    raise Exception('No line starting with prefix: ' + prefix + ' found in list!')


def zero_index_activity(act):
    return int(act) - 1


def extract_activity_precedence(lines):
    pre_data = []
    pre_data_line = {}
    ix = index_of_line_starting_with('PRECEDENCE RELATIONS:', lines)
    # initialize precidence dictionary
    for act in range(act_count):
        # pyomo indexed elements required format
        pre_data_line[act] = {'index': act, 'value': []}

    for line in lines[ix + 2:ix + 2 + act_count]:
        parts = line.split()
        act = zero_index_activity(parts[0])
        succs = parts[3:]
        # change successor format to predecessor
        for succ in succs:
            idx = zero_index_activity(succ)
            pre_data_line[idx]['value'].append(act)

        pre_data.append(pre_data_line[act])

    return pre_data


def extract_activity_attributes(lines):
    r_cons = []
    act_proc = []
    ix = index_of_line_starting_with('REQUESTS/DURATIONS:', lines)

    # dummy source and sink activities are skipped.
    for line in lines[ix + 4:ix + 4 + act_count - 2]:
        parts = line.split()
        act = zero_index_activity(parts[0])
        act_proc.append({'index': act, 'value': int(parts[2])})
        for r in range(r_count):
            r_cons.append({'index': [act, 1 + r], 'value': int(parts[3 + r])})
            
    return r_cons, act_proc


def extract_resource_capacities(lines):
    rcap_data = []
    ix = index_of_line_starting_with('RESOURCEAVAILABILITIES', lines)

    rlist = list(map(lambda capstr: int(capstr), lines[ix + 2].split()))
    for idx in range(1, len(rlist) + 1):
        rcap_data.append({'index': idx, 'value': rlist[idx - 1]})

    return rcap_data


def parse_lines(lines):
    global act_count, r_count

    act_count = extract_val(lines, 'jobs (incl. supersource/sink', 'Unable to extract number of acts!')
    r_count = extract_val(lines, '- renewable', 'Unable to extract number of resources!')
    r_cons, act_proc = extract_activity_attributes(lines)
    r_cap = extract_resource_capacities(lines)
    pre_data = extract_activity_precedence(lines)

    data = {
        'act_count': act_count - 2,  # remove source and sink from act count
        'r_count': r_count,
        'act_pre': pre_data,
        'r_cap': r_cap,
        'r_cons': r_cons,
        'act_proc': act_proc

    }

    return data


def convert_file(smfilename):
    smpath = os.path.split(smfilename)
    instname = smpath[1].split('.')[0]
    smdir = smpath[0].split('sm')
    with open(smfilename, 'r') as fp:
        lines = fp.readlines()
        data = parse_lines(lines)
        with open(smdir[0] + 'json' + smdir[1] + '/' + instname + '.json', 'w') as jsonfp:
            jsonfp.write(json.dumps(data, sort_keys=False, indent=4, separators=(',', ': ')))


convert_file(sys.argv[1])