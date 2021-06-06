import sys
from datetime import datetime
import pyomo.dataportal as dp
import pyomo.environ as pyo
import rcpsp_con as rcpsp

data = dp.DataPortal()

instance_dir = 'data/instances/json/{instance_dir}/'.format(instance_dir=sys.argv[1])
instance_name = sys.argv[2]

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

# Custom sets
# Set P - No hard precedence - overlapping activities
P = set()
S = set()
K = set()
for i in range(1, sink):
    for j in range(1, sink):
        if i != j and i not in data['act_pre'][j] and j not in data['act_pre'][i]:
            K.update([(i, j)])
            in_s = False
            for k in range(1, data['r_count'] + 1):
                if data['r_cons'][i, k] + data['r_cons'][j, k] > data['r_cap'][k]:
                    S.update([(i, j)])
                    in_s = True
                    break
            if not in_s:
                P.update([(i, j)])

data['P'] = P
data['S'] = S
data['K'] = K

instance = rcpsp.model.create_instance(data)
#instance.pprint()

# Solve instance and print results
opt = pyo.SolverFactory('cplex')
opt.options['threads'] = 1
results = opt.solve(instance, load_solutions=True)


results.write(filename='data/results/continuous/{instance_name}_results_{timestamp}.json'
              .format(instance_name=instance_name, timestamp=datetime.now().strftime("%d_%m_%Y_%H_%M_%S")), format='json')


#instance.display()
