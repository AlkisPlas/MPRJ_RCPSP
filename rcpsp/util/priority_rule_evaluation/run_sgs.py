import argparse

import pyomo.dataportal as dp
import pyomo.environ as pyo
from pyomo.core.base.component import CloneError
from rcpsp.heuristics.backward_recursion import BackwardRecursion
from rcpsp.heuristics.forward_recursion import get_earliest_times
from rcpsp.heuristics.sgs import serial_schedule_generation

import rcpsp.formulations.perfect_knowledge.continuous.rcpsp_con as rcpsp

parser = argparse.ArgumentParser()
parser.add_argument("dir") 
parser.add_argument("instance") 
parser.add_argument("-pr", "--use_pr", action="store_true", default=False) 

args = parser.parse_args()

instance_dir = 'data/instances/json/{instance_dir}/'.format(instance_dir=args.dir)
instance_name = args.instance

data = dp.DataPortal()
data.load(filename=instance_dir + instance_name + '.json')

act_count = data['act_count']
act_pre = data['act_pre']    
r_count = data['r_count']
r_cons = data['r_cons']
r_cap = data['r_cap']
act_proc = data['act_proc']

# Initialize dummy source and sink activities
source = 0
sink = act_count + 1

act_proc[source] = 0
act_proc[sink] = 0

for r in range(1, r_count + 1):
    r_cons[source, r] = 0
    r_cons[sink, r] = 0

# Calculate earliest start and finish times
est, eft = get_earliest_times(sink, act_pre, act_proc)
data['est'] = est
data['eft'] = eft

# Calculate initial latest start and finish times. Upper bound is the sum of processing times
br_init = BackwardRecursion(sink, sum(act_proc.values()), act_pre, act_proc)
lst_init, lft_init = br_init.get_latest_times()

# Tighten upper bound with SGS
upper_bound = serial_schedule_generation(
    act_count, act_proc, act_pre, r_count, r_cons, r_cap, lft_init, args.use_pr)

print(upper_bound)