import rcpsp_dis as rcpsp
import pyomo.environ as pyo
import pyomo.dataportal as dp
from datetime import datetime

data = dp.DataPortal()
data.load(filename='data/test_data/rcpsp_con_test_data.json')

#model preprocessing
data['upper_bound'] = {None : sum(data['act_proc'].values())}

#initialize dummy activities
act_count = data['act_count']
data['act_proc'][0] = 0
data['act_proc'][act_count + 1] = 0

for r in range(1, data['r_count'] + 1):
    data['r_cons'][0, r] = 0
    data['r_cons'][act_count + 1, r] = 0

instance = rcpsp.model.create_instance(data)
#instance.pprint()

opt = pyo.SolverFactory('cplex')
opt.options['threads'] = 1

results = opt.solve(instance, load_solutions=True)
#results.write(filename='results/results_dis_' + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + '.json', format='json')

print(results.solver)
for v in instance.component_data_objects(pyo.Var):
    if int(v.value) == 1:
        print (str(v), int(v.value))