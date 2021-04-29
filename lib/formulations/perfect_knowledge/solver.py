import rcpsp_cont as rcpsp
import pyomo.environ as pyo
import pyomo.dataportal as dp

data = dp.DataPortal()
data.load(filename='rcpsp_con_test_data.json')

instance = rcpsp.model.create_instance(data)
instance.pprint()

opt = pyo.SolverFactory('cplex')
#opt.options['threads'] = 2
opt.solve(instance) 

instance.act_fin.pprint()