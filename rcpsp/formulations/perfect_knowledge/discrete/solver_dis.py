import sys
from datetime import datetime
import pyomo.dataportal as dp
import pyomo.environ as pyo
import rcpsp_dis as rcpsp
from rcpsp.heuristics.sgs import serial_schedule_generation
from rcpsp.heuristics.forward_recursion import get_earliest_times
from rcpsp.heuristics.backward_recursion import BackwardRecursion

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

# Calculate earliest start and finish times
est, eft = get_earliest_times(sink + 1, act_pre, act_proc)
data['est'] = est
data['eft'] = eft

# Calculate initial latest start and finish times. Upper bound is the sum of processing times
br_init = BackwardRecursion(sink, sum(act_proc.values()), act_pre, act_proc)
lst_init, lft_init = br_init.get_latest_times()

# Tighten upper bound with SGS
upper_bound = serial_schedule_generation(
    act_count, act_proc, act_pre, r_count, r_cons, r_cap, lft_init)

# Calculate latest start and finish times using the new upper bound
br = BackwardRecursion(sink, upper_bound, act_pre, act_proc)
lst, lft = br.get_latest_times()

data['lst'] = lst
data['lft'] = lft
data['upper_bound'] = {None: upper_bound}

# Initialize variable sparse index set 
x_set_init = []
for act in range(sink + 1):
    for t in range(est[act], lst[act] + 1):
        x_set_init.append((act, t))
data["x_set_init"] = x_set_init

print('Preprocessing phase complete. Sending to solver...')
instance = rcpsp.model.create_instance(data)
#instance.pprint()

# Solve instance and print results
opt = pyo.SolverFactory('cplex')
opt.options['threads'] = 2
opt.options['timelimit'] = 600
results = opt.solve(instance, load_solutions=True)

results.write(filename='data/results/discrete/{instance_dir}/{instance_name}_results_{timestamp}.json'
              .format(instance_dir=sys.argv[1], instance_name=instance_name, timestamp=datetime.now().strftime("%d_%m_%Y_%H_%M_%S")), format='json')

'''
print(results.solver)
for v in instance.component_data_objects(pyo.Var):
    if v.value is not None and int(v.value) == 1:
        act = str(v).split('[')[1].split(',')
        print('Activity {act} starts at {start}'.format(act=act[0], start=act[1].split(']')[0]))
'''