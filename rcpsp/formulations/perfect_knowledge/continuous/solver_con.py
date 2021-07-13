import sys
from datetime import datetime
from pyomo.core.base.component import CloneError
import pyomo.dataportal as dp
import pyomo.environ as pyo
import rcpsp_con as rcpsp
from rcpsp.heuristics.sgs import serial_schedule_generation

data = dp.DataPortal()

instance_dir = 'data/instances/json/{instance_dir}/'.format(instance_dir=sys.argv[1])
instance_name = sys.argv[2]

print('\nSolving instance:' + instance_name)

data.load(filename=instance_dir + instance_name + '.json')

act_count = data['act_count']
act_proc = data['act_proc']
act_pre = data['act_pre']
r_count = data['r_count']
r_cons = data['r_cons']
r_cap = data['r_cap']

# Initialize dummy source and sink activities
source = 0
sink = act_count + 1

act_proc[source] = 0
act_proc[sink] = 0

for r in range(1, r_count + 1):
    r_cons[source, r] = 0
    r_cons[sink, r] = 0

upper_bound = sum(act_proc.values())

# Calculate earliest starting and finishing times
est = {}
for act in range(sink + 1):
    est[act] = max((est[pre] + act_proc[pre]
                   for pre in act_pre[act]), default=0)
eft = {act : val + act_proc[act] for act, val in est.items()}
data['est'] = est
data['eft'] = eft

# Calculate latest starting and finishing times
lst_init = {}

# Calculate initial upper bound as sum of processing times
lst_init[sink] = sum(act_proc.values())
visited = []

def get_latest_starting_time(act, lst):
    for pre in act_pre[act]:
        if pre not in visited:
            visited.append(pre)
            lst[pre] = lst[act] - act_proc[pre]
            get_latest_starting_time(pre, lst)

get_latest_starting_time(sink, lst_init)
lft_init = {act : val + act_proc[act] for act, val in lst_init.items()}

upper_bound = serial_schedule_generation(
    act_count, act_proc, act_pre, r_count, r_cons, r_cap, lft_init)

lst = {}
lst[sink] = upper_bound
visited.clear()

get_latest_starting_time(sink, lst)
lft = {act : val + act_proc[act] for act, val in lst.items()}

data['lst'] = lst
data['lft'] = lft
data['upper_bound'] = {None: upper_bound}

# Get transitive closure of graph
# TODO - merge with the DFS above
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

for i, j in C:
    if (i, j) not in C and lft[i] <= est[j]:
        D.update([(i, j)])

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
#instance.pprint()

# Solve instance and print results
opt = pyo.SolverFactory('cplex')
opt.options['threads'] = 2
opt.options['timelimit'] = 600
#opt.options['mipgap'] = 0.05
results = opt.solve(instance, load_solutions=True)


results.write(filename='data/results/continuous/{instance_dir}/{instance_name}_results_{timestamp}.json'
              .format(instance_dir=sys.argv[1], instance_name=instance_name, timestamp=datetime.now().strftime("%d_%m_%Y_%H_%M_%S")), format='json')

print('Done')

#instance.display()
