import rcpsp_dis as rcpsp
import pyomo.environ as pyo
import pyomo.dataportal as dp
from datetime import datetime

data = dp.DataPortal()
instance_dir = 'data/instances/json/j60/'
instance_name = 'j602_9'
data.load(filename=instance_dir + instance_name + '.json')

#Initialize dummy source and sink activities
source = 0
sink = data['act_count'] + 1

data['act_proc'][source] = 0
data['act_proc'][sink] = 0

for r in range(1, data['r_count'] + 1):
    data['r_cons'][source, r] = 0
    data['r_cons'][sink, r] = 0

#Calculate earliest starting times
est = {}
for act in range(sink + 1):
    est[act] = max((est[pre] + data['act_proc'][pre] for pre in data['act_pre'][act]), default=0)
data['est'] = est

#Calculate latest starting times
upper_bound = sum(data['act_proc'].values())
data['upper_bound'] = {None : upper_bound}

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
data['lst'] = lst

#Solve instance and print results
instance = rcpsp.model.create_instance(data)
#instance.pprint()

opt = pyo.SolverFactory('cplex')
opt.options['threads'] = 1
results = opt.solve(instance, load_solutions=True)
results.write(filename='data/results/' + instance_name + '_results_dis_' + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + '.json', format='json')

print(results.solver)
for v in instance.component_data_objects(pyo.Var):
    if int(v.value) == 1:
        act = str(v).split('[')[1].split(',')
        print ('Activity {act} starts at {start}'.format(act = act[0], start = act[1].split(']')[0]))
