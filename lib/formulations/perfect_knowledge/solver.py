import rcpsp_dis as rcpsp
import pyomo.environ as pyo
import pyomo.dataportal as dp

data = dp.DataPortal()
data.load(filename='data/test_data/rcpsp_con_test_data.json')

#model preprocessing
data.__setitem__('upper_bound', {None : sum(data['act_proc'].values())})

act_count = data['act_count']
data['act_proc'][0] = 0
data['act_proc'][act_count + 1] = 0

for r in range(1, data['r_count'] + 1):
    data['r_cons'][0, r] = 0
    data['r_cons'][act_count + 1, r] = 0

instance = rcpsp.model.create_instance(data)
instance.pprint()

opt = pyo.SolverFactory('cplex')
#opt.options['threads'] = 2

results = opt.solve(instance)

#print(results.solver)
instance.x_jt.pprint()