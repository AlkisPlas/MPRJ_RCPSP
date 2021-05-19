import rcpsp_dis as rcpsp
import pyomo.environ as pyo
import pyomo.dataportal as dp
from datetime import datetime

data = dp.DataPortal()
data.load(filename='data/test_data/rcpsp_con_test_data.json')

#Initialize dummy source and sink activities
source = 0
sink = data['act_count'] + 1

data['act_proc'][source] = 0
data['act_proc'][sink] = 0

for r in range(1, data['r_count'] + 1):
    data['r_cons'][source, r] = 0
    data['r_cons'][sink, r] = 0

#Calculate latest starting time.
upper_bound = sum(data['act_proc'].values())
data['upper_bound'] = {None : upper_bound}

lt = {}
lt[sink] = upper_bound
visited = []
def get_latest_starting_time(act):
    for pre in data['act_pre'][act]:
        if pre not in visited:
            visited.append(pre)
            lt[pre] = lt[act] - data['act_proc'][pre]
            get_latest_starting_time(pre)
            
            
get_latest_starting_time(sink)
data['lst'] = lt

#Solve instance and print results
instance = rcpsp.model.create_instance(data)
instance.pprint()

opt = pyo.SolverFactory('cplex')
opt.options['threads'] = 1

results = opt.solve(instance, load_solutions=True)
#results.write(filename='results/results_dis_' + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + '.json', format='json')

print(results.solver)
for v in instance.component_data_objects(pyo.Var):
    if int(v.value) == 1:
        print (str(v), int(v.value))