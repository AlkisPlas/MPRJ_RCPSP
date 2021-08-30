from pyomo.environ import *
from pyomo.bilevel import *
import logging

for name in logging.Logger.manager.loggerDict.keys():
    logging.getLogger(name).setLevel(logging.CRITICAL)

'''
A bilevel formulation for the RCPSP. Time horizon is divided into discrete intervals 
This is a minimax formulation that aims to minimize the worst case makespan.
Activity durations lie within a budgeted uncertainty set.
Number of activities that can attain their worst case values are controlled 
by parameter GAMMA. Worst case deviation is controlled by parameter THETA.


Based on the formulation of Aristide Mingozzi, Vittorio Maniezzo, Salvatore Ricciardelli, Lucio Bianco, (1998) 
An Exact Algorithm for the Resource-Constrained Project Scheduling Problem Based on a New Mathematical Formulation. 
Management Science 44(5):714-729.
'''
model = AbstractModel(name="RCPSP_DISCRETE_ROBUST")

# Activity set
model.act_count = Param(within=NonNegativeIntegers)
model.act_set = RangeSet(0, model.act_count + 1)

# Activity Precedence Set
model.act_pre = Param(model.act_set, mutable=True, domain=Any)

# Nominal activity processing times
model.act_proc = Param(model.act_set, within=NonNegativeReals)
# Worst case duration factor
model.THETA = Param()
# Uncertainty budget
model.GAMMA = Param()

# Resource set
model.r_count = Param(within=NonNegativeIntegers, domain=Any)
model.r_set = RangeSet(model.r_count)

# Available units of all resources
model.r_cap = Param(model.r_set)

# Resource consumption of activities
model.r_cons = Param(model.act_set, model.r_set, within=NonNegativeIntegers)

# Period Set
model.upper_bound = Param(within=NonNegativeIntegers)
model.period_set = RangeSet(0, model.upper_bound)

# Activity time windows
model.est = Param(model.act_set, within=NonNegativeIntegers)
model.lst = Param(model.act_set, within=NonNegativeIntegers)

'''
Outer level decision variables.
Uncertain activity duration factor.
A choice of delta factors represents a realization of the uncertainty set (i.e. one duration vector)
This is an adversarial problem where the adversary tries to distribute GAMMA 
units of delay with the aim to maximize the minimum makespan amongst all realizations.
'''
model.delta = Var(model.act_set, within=NonNegativeReals, initialize=0)

def uncertainty_budget_constraint(m):
    return sum(m.delta[n] for n in m.act_set) <= m.GAMMA

model.uncertainty_budget_constraint = Constraint(rule=uncertainty_budget_constraint)


def delta_upper_bound_constraint(m, n):
    return m.delta[n] <= 1

model.delta_upper_bound_constraint = Constraint(model.act_set, rule=delta_upper_bound_constraint)


# Inner level binary decision variables. If activity j starts at period t
model.x_set_init = Set(dimen=2)
model.inner = SubModel(fixed=model.delta)
model.inner.x = Var(model.x_set_init, within=Binary, initialize=False, dense=False)


# Resource capacity constraint for resource r at time t
def resource_capacity_constraint(sub_m, r, t):
    M = sub_m.model()
    r_sum = sum(
        M.r_cons[act, r] * sub_m.x[act, q]
        for act in M.act_set
        for q in range(
            max(0, t - round(M.act_proc[act] * (1 + value(M.delta[act]) * M.THETA)) + 1), t + 1
        ) if q >= M.est[act] and q <= M.lst[act]
    )
    
    if isinstance(r_sum, int):
        return Constraint.Skip

    return r_sum <= M.r_cap[r]


model.inner.resource_constraint = Constraint(
    model.r_set, model.period_set, rule=resource_capacity_constraint)


# Precedence constraint for activity n
def activity_precedence_constraint(sub_m, n, pre_n):
    M = sub_m.model()

    # The dummy source doesn't have predecessors
    if n == 0:
        return Constraint.Skip

    if pre_n in value(M.act_pre[n]):
        return sum(t * sub_m.x[pre_n, t] for t in range(M.est[pre_n], M.lst[pre_n] + 1)) \
            <= sum(t * sub_m.x[n, t] for t in range(M.est[n], M.lst[n] + 1)) - M.act_proc[n] * (1 + M.delta[n] * M.THETA)

    return Constraint.Skip


model.inner.precedence_constraint = Constraint(
    model.act_set, model.act_set, rule=activity_precedence_constraint)


# Non preemption constraint for activity n
def no_preemption_constraint(sub_m, n):
    M = sub_m.model()
    return sum(sub_m.x[n, t] for t in range(M.est[n], M.lst[n] + 1)) == 1


model.inner.no_preemption_constraint = Constraint(
    model.act_set, rule=no_preemption_constraint)


# Objective - Minimize finish time of the last activity
def finish_time_objective(sub_m):
    M = sub_m.model()
    last_activity = value(M.act_count) + 1
    return sum(t * sub_m.x[last_activity, t] for t in range(M.est[last_activity], M.lst[last_activity] + 1))

model.inner.OBJ = Objective(rule=finish_time_objective, sense=minimize)

# Adversarial Outer level Objective - Worst case makespan     
model.OBJ = Objective(expr=model.inner.OBJ, sense=maximize)