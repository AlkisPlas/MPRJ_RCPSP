from pyomo.environ import *
from pyomo.bilevel import *

import logging

for name in logging.Logger.manager.loggerDict.keys():
    logging.getLogger(name).setLevel(logging.CRITICAL)
    
'''
A bilevel formulation for the RCPSP with a continuous time horizon. 
This is a minimax formulation that aims to minimize the worst case makespan.
Activity durations lie within a budgeted uncertainty set.
Number of activities that can attain their worst case values are controlled 
by parameter GAMMA. Worst case deviation is controlled by parameter THETA.
'''
model = AbstractModel(name="RCPSP_CONTINUOUS_ROBUST")

# Activity set
model.act_count = Param(within=NonNegativeIntegers)
model.act_set = RangeSet(0, model.act_count + 1)

# Activity Precedence Set
model.act_pre = Param(model.act_set, domain=Any)

# Resource set
model.r_count = Param(within=NonNegativeIntegers, domain=Any)
model.r_set = RangeSet(model.r_count)

# Available units of all resources
model.r_cap = Param(model.r_set)

# Resource consumption of activities
model.r_cons = Param(model.act_set, model.r_set,
                     within=NonNegativeIntegers, mutable=True)

# Nominal activity processing times
model.act_proc = Param(model.act_set, within=NonNegativeReals)
# Worst case duration factor
model.THETA = Param()
# Uncertainty budget
model.GAMMA = Param()

# Activity time windows
model.est = Param(model.act_set, within=NonNegativeIntegers)
model.lst = Param(model.act_set, within=NonNegativeIntegers)
model.eft = Param(model.act_set, within=NonNegativeIntegers)
model.lft = Param(model.act_set, within=NonNegativeIntegers)
model.upper_bound = Param(within=NonNegativeIntegers)

# Modelling sets.
model.B = Set(dimen=2)
model.C = Set(dimen=2)
model.G = Set(dimen=2)
model.K = Set(dimen=2)
model.S = Set(dimen=2)
model.P = Set(dimen=2)

'''
Outer level decision variables.
Uncertain activity duration factor.
A choice of delta factors represents a realization of the uncertainty set (i.e. one duration vector)
This is an adversarial problem where the adversary tries to distribute GAMMA 
units of delay with the aim to maximize the minimum makespan amongst all realizations.
'''
model.delta = Var(model.act_set, within=NonNegativeReals)

def uncertainty_budget_constraint(m):
    return sum(m.delta[n] for n in m.act_set) <= m.GAMMA

model.uncertainty_budget_constraint = Constraint(rule=uncertainty_budget_constraint)


def delta_upper_bound_constraint(m, n):
    return m.delta[n] <= 1

model.delta_upper_bound_constraint = Constraint(model.act_set, rule=delta_upper_bound_constraint)

'''
Inner level Decision variables.
Activity start and finishing times
For every realization of the uncertainty set, the inner problem finds the minimum makespan
'''
model.inner = SubModel(fixed=model.delta)
model.inner.start = Var(model.act_set, within=NonNegativeReals)
model.inner.fin = Var(model.act_set, within=NonNegativeReals, bounds=(0, model.upper_bound))

'''
Execution sequence variables.

For activities that cannot be executed in parallel x[i,j] = 1 if fin[i] <= start[j], 0 otherwise
For activities that can be executed in parallel x[i,j] = 1 if start[i] <= start[j], 0 otherwise
'''
model.inner.x_set = (model.B | model.G) - model.K
model.inner.x = Var(model.inner.x_set, within=Binary)

'''
Overlapping activity variables

z[i, j] = 1 (i overlaps j) if 
start[i] <= start[j] and fin[i] > start[j]
If i overlaps i then z[i, j] - x[j, i] = 1
'''
model.inner.z = Var(model.P, within=Binary)

# Correlate the finishing and starting time of activities
def start_finish_correlation(sub_m, n):
    M = sub_m.model()
    return sub_m.fin[n] == sub_m.start[n] + M.act_proc[n] * (1 + M.delta[n] * (M.THETA))

model.inner.start_finish_correlation_constraint = Constraint(
    model.act_set, rule=start_finish_correlation)


# Constraints for activities with known precedence requirements
def activity_hard_precedence(sub_m, n, pre_n):
    M = sub_m.model()
    if pre_n in M.act_pre[n]:
        return sub_m.fin[pre_n] <= sub_m.start[n]

    return Constraint.Skip

model.inner.hard_precedence_constraint = Constraint(
    model.act_set, model.act_set, rule=activity_hard_precedence)

''' 
Precedence constraints for activities that can't overlap

If i is scheduled before j (xij = 1 -> xji = 0) then i must finish before j starts (fin[i] <= start[j])
because there are not enough resources for them to overlap. If j is scheduled before i (xji = 1)
then the constraint is skipped because fin[i] - start[j] <= lft[i] - est[j] always holds
'''
def activity_non_overlapping_precedence(sub_m, i, j):
    M = sub_m.model()
    return sub_m.fin[i] <= sub_m.start[j] + (M.upper_bound) * sub_m.x[j, i]
        
model.inner.activity_non_overlapping_precedence_constraint = Constraint(
    model.S, rule=activity_non_overlapping_precedence)

'''
Precedence constraints for activities that can overlap

If i is scheduled before j (xij = 1 -> xji = 0) then i must start before j starts (start[i] <= start[j])
as dictated by the decision variables. If j is scheduled before i (xji = 1) then the constraint is skipped 
because start[i] - start[j] <= lst[i] - est[j] always holds
'''
def activity_overlapping_precedence_1(sub_m, i, j):
    M = sub_m.model()
    if i > j:
        return sub_m.start[j] <= sub_m.start[i] + (M.upper_bound) * sub_m.x[i, j]

    return Constraint.Skip

model.inner.activity_overlapping_precedence_constraint_1 = Constraint(
    model.P, rule=activity_overlapping_precedence_1)


def activity_overlapping_precedence_2(sub_m, i, j):
    M = sub_m.model()
    if i > j:
        return sub_m.start[i] + 0.1 <= sub_m.start[j] + (M.upper_bound + 0.1) * sub_m.x[j, i]

    return Constraint.Skip

model.inner.activity_overlapping_precedence_constraint_2 = Constraint(
    model.P, rule=activity_overlapping_precedence_2)


# For activities without hard precedence constraints, avoid execution cycles.
def no_execution_cycles(sub_m, i, j):
    M = sub_m.model()
    if i > j and (i, j) not in M.K:
        return sub_m.x[i, j] + sub_m.x[j, i] == 1

    return Constraint.Skip

model.inner.no_execution_cycles_constraint = Constraint(
    model.act_set, model.act_set, rule=no_execution_cycles)

'''
Define overlapping decision variables.
If z[i, j] is 0 then i and j are not overlapping meaning that i finishes before j starts.
If z[i, j] is 1 then the constraint is skipped because fin[i] - start[j] <= lft[i] - est[j] always holds
'''
def overlapping_variables(sub_m, i, j):
    M = sub_m.model()
    return sub_m.fin[i] <= sub_m.start[j] + (M.upper_bound) * sub_m.z[i, j]

model.inner.overlapping_variables_constraint = Constraint(
    model.P, rule=overlapping_variables)


# Resource capacity constraint for resource r
def resource_capacity_constraint(sub_m, i, k):
    M = sub_m.model()
    return M.r_cons[i, k] + sum(M.r_cons[j, k] * (sub_m.z[j, a] - sub_m.x[a, j]) for a, j in M.P if i == a) <= M.r_cap[k]

model.inner.resource_constraint = Constraint(
    model.act_set, model.r_set, rule=resource_capacity_constraint)

'''
For activities that can be executed in parallel,
if i starts before j then j must be overlapping i.
'''
def tighten_decision_variables(sub_m, i, j):
    return sub_m.x[i, j] <= sub_m.z[j, i]

model.inner.tighten_decision_variables_constraint = Constraint(
    model.P, rule=tighten_decision_variables)


# Inner level Objective - Minimize finish time of the last activity
def finish_time_objective_inner(sub_m):
    M = sub_m.model()
    return sub_m.fin[value(M.act_count) + 1]

model.inner.OBJ = Objective(rule=finish_time_objective_inner, sense=minimize)

# Outer level Objective - Maximize total duration
def finish_time_objective_outer(m):
    return m.inner.fin[value(m.act_count) + 1]
    
model.OBJ = Objective(rule=finish_time_objective_outer, sense=maximize)