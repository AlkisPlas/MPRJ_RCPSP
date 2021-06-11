import sys
from datetime import datetime
from pyomo.core.base.component import CloneError
import pyomo.dataportal as dp
import pyomo.environ as pyo
import rcpsp_con as rcpsp

data = dp.DataPortal()

instance_dir = 'data/instances/json/{instance_dir}/'.format(instance_dir=sys.argv[1])
instance_name = sys.argv[2]

#instance_dir = 'data/test_data/'
#instance_name = 'rcpsp_test_instance_2'

print('\nSolving instance:' + instance_name)

data.load(filename=instance_dir + instance_name + '.json')

# Initialize dummy source and sink activities
source = 0
sink = data['act_count'] + 1

data['act_proc'][source] = 0
data['act_proc'][sink] = 0

for r in range(1, data['r_count'] + 1):
    data['r_cons'][source, r] = 0
    data['r_cons'][sink, r] = 0

# Calculate initial upper bound as sum of processing times
upper_bound = sum(data['act_proc'].values())
data['upper_bound'] = {None: upper_bound}

# Calculate earliest starting and finishing times
est = {}
for act in range(sink + 1):
    est[act] = max((est[pre] + data['act_proc'][pre]
                   for pre in data['act_pre'][act]), default=0)
eft = {act : val + data['act_proc'][act] for act, val in est.items()}
data['est'] = est
data['eft'] = eft

# Calculate latest starting and finishing times
#TODO - Change the DFS to CPM
lst = {}
lst[sink] = upper_bound
visited = []

def get_latest_starting_time(act):
    for pre in data['act_pre'][act]:
        if pre not in visited:
            visited.append(pre)
            lst[pre] = lst[act] - data['act_proc'][pre]
            get_latest_starting_time(pre)

get_latest_starting_time(sink)
lft = {act : val + data['act_proc'][act] for act, val in lst.items()}
data['lst'] = lst
data['lft'] = lft


# Get transitive closure of graph
# TODO - merge with the DFS above
C = set()
def get_transitive_closure(root, act):
    for pre in data['act_pre'][act]:
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
        if i!=j and (data['r_cons'][i, k] > 0 and data['r_cons'][j, k] > 0 for k in range(1, data['r_count'] + 1)):
            B.update([(i, j)])

for i, j in B:
    for k in range(1, data['r_count'] + 1):
        if data['r_cons'][i, k] + data['r_cons'][j, k] > data['r_cap'][k]:
            G.update([(i, j)])
            break

for i, j in C:
    if (i, j) not in C and lft[i] <= est[j]:
        D.update([(i, j)])


data['B'] = B
data['C'] = C
data['G'] = G
K = C.union(D)
data['K'] = K
data['S'] = G.difference(K)
data['P'] = B.difference(G.union(K))

print('Preprocessing phase complete. Sending to solver...')
instance = rcpsp.model.create_instance(data)
#instance.pprint()

# Solve instance and print results
opt = pyo.SolverFactory('cplex')
opt.options['threads'] = 2
opt.options['timelimit'] = 600
results = opt.solve(instance, load_solutions=True)


results.write(filename='data/results/continuous/{instance_dir}/{instance_name}_results_{timestamp}.json'
              .format(instance_dir=sys.argv[1], instance_name=instance_name, timestamp=datetime.now().strftime("%d_%m_%Y_%H_%M_%S")), format='json')

print('Done')

#instance.display()
