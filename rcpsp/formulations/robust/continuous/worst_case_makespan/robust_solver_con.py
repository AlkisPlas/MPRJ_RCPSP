import argparse
import json
import math
from datetime import datetime

import pyomo.dataportal as dp
import pyomo.environ as pyo
from pyomo.core.base.component import CloneError
from rcpsp.heuristics.backward_recursion import BackwardRecursion
from rcpsp.heuristics.forward_recursion import get_earliest_times
from rcpsp.heuristics.sgs import serial_schedule_generation

import robust_rcpsp_con as rcpsp

# Metasolvers are here
# import pyomo.bilevel.plugins

parser = argparse.ArgumentParser()
parser.add_argument("dir") 
parser.add_argument("instance")
parser.add_argument("-theta", "--theta", type=float, default=0.0) 
parser.add_argument("-gamma", "--gamma", type=float, default=0.0) 
parser.add_argument("-p", "--perturb", action="store_true", default=False) 
parser.add_argument("-d", "--display", action="store_true", default=False) 
parser.add_argument("-s", "--store", action="store_true", default=False) 
args = parser.parse_args()

instance_dir = 'data/instances/json/{instance_dir}/'.format(instance_dir=args.dir)
instance_name = args.instance

data = dp.DataPortal()
data.load(filename=instance_dir + instance_name + '.json')

act_count = data['act_count']
act_proc = data['act_proc']
act_pre = data['act_pre']
r_count = data['r_count']
r_cons = data['r_cons']
r_cap = data['r_cap']

# Worst case duration factor
THETA = args.theta
data['THETA'] = {None: THETA}

# Uncertainty budget
GAMMA = args.gamma
data['GAMMA'] = {None: GAMMA}

print('\nSolving instance: {instance}. Using GAMMA={GAMMA}, THETA={THETA}'.format(instance=instance_name, GAMMA=GAMMA,THETA=THETA))

# Initialize dummy source and sink activities
source = 0
sink = act_count + 1

act_proc[source] = 0
act_proc[sink] = 0

for r in range(1, r_count + 1):
    r_cons[source, r] = 0
    r_cons[sink, r] = 0

act_proc_worst = {}
for act in act_proc:
    act_proc_worst[act] = round(act_proc[act] * (1 + THETA))
data['act_proc_worst'] = act_proc_worst

# Calculate initial latest start and finish times. Upper bound is the sum of processing times
br_init = BackwardRecursion(sink, sum(act_proc_worst.values()), act_pre, act_proc_worst)
lst_init, lft_init = br_init.get_latest_times()

# Tighten upper bound with SGS
upper_bound = serial_schedule_generation(
    act_count, act_proc_worst, act_pre, r_count, r_cons, r_cap, lft_init)

# Calculate latest start and finish times using the new upper bound
br = BackwardRecursion(sink, upper_bound, act_pre, act_proc_worst)
lst, lft = br.get_latest_times()

data['lst'] = lst
data['lft'] = lft
data['upper_bound'] = {None: upper_bound}

# Get transitive closure of graph
C = set()
def get_transitive_closure(root, act):
    for pre in act_pre[act]:
        if (pre, root) not in C:
            C.update([(pre, root)])
            C.update([(root, pre)])
            get_transitive_closure(root, pre)

for act in range(sink + 1):
    get_transitive_closure(act, act)

# Custom sets
B = set()
D = set()
G = set()
for i in range(1, sink):
    for j in range(1, sink):
        if i!=j and (r_cons[i, k] > 0 and r_cons[j, k] > 0 for k in range(1, r_count + 1)):
            B.update([(i, j)])

for i, j in B:
    for k in range(1, r_count + 1):
        if r_cons[i, k] + r_cons[j, k] > r_cap[k]:
            G.update([(i, j)])
            break


# Activities sharing at least one resource
data['B'] = B
# Precedence transitive closure. All hard precedence relationships
data['C'] = C
# Activities that cannot be executed in parallel due to resource cap violations.
data['G'] = G
K = C.union(D)
data['K'] = K
# Activities that cannot overlap due to resource capacity limitations, 
# excluding those with known precedence relations
data['S'] = G.difference(K)
# Activities that can overlap
data['P'] = B.difference(G.union(K))

print('Preprocessing phase complete. Sending to solver...')
instance = rcpsp.model.create_instance(data)

''' 
Apply the bilevel linear duality metasolver.
The metasolver will perform a series of transformations
using duality and linearization. The cplex solver will
be used to solve the transformed instance.
'''
opt = pyo.SolverFactory('bilevel_ld')
opt.options['solver'] = 'cplex'

results = opt.solve(instance, load_solutions=True)

if args.store:
    # Get the inner solver results from the temp file.
    with open("data/results/robust/continuous/worst_case_makespan/inner_results.json", "r") as jsonFile:
        data = json.load(jsonFile)

    # Set the inner only time to the total time 
    data['Solver'][0]['User time'] = results.solver.wallclock_time

    # Dump to the correct directory
    with open('data/results/robust/continuous/worst_case_makespan/{instance_dir}/{instance_name}_results_{timestamp}.json'
                .format(instance_dir=args.dir, instance_name=instance_name, timestamp=datetime.now().strftime("%d_%m_%Y_%H_%M_%S")), "w") as jsonFile:
        json.dump(data,jsonFile, indent=4)

if args.display:
    instance.inner.fin.display()

print('Worst case makespan:' + str(instance.inner.OBJ()))
#print(round(instance.inner.OBJ()))