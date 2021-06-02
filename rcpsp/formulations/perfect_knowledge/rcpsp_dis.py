from pyomo.environ import *

'''
Binary Integer Programming formulation for the RCPSP.
Time horizon is divided into discrete intervals.
'''
model = AbstractModel(name="RCPSP_DISCRETE")

# Activity set
model.act_count = Param(within=NonNegativeIntegers)
model.act_set = RangeSet(0, model.act_count + 1)

# Activity Precedence Set
model.act_pre = Param(model.act_set, mutable=True, domain=Any)

# Activity processing times
model.act_proc = Param(model.act_set, within=NonNegativeIntegers)

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

# Decision variables. If activity j starts at period t
model.x_set_init = Set(dimen=2)
model.x_jt = Var(model.x_set_init, within=Binary, initialize=False, dense=False)


# Resource capacity constraint for resource r at time t
def resource_capacity_constraint(m, r, t):

    for act in m.act_set:
        if t < m.est[act] or t > m.lst[act]:
            return Constraint.Skip

    return sum(
        m.r_cons[act, r] * m.x_jt[act, q]
        for act in m.act_set
        for q in range(
            max(0, t - value(m.act_proc[act]) + 1), t + 1
        )  
    ) <= m.r_cap[r]

model.resource_constraint = Constraint(
    model.r_set, model.period_set, rule=resource_capacity_constraint)


# Precedence constraint for activity n
def activity_precedence_constraint(m, n, pre_n):
    if n == 0:
        return Constraint.Skip

    if pre_n in value(m.act_pre[n]):
        return sum(t * m.x_jt[pre_n, t] for t in range(m.est[pre_n], m.lst[pre_n])) \
            <= sum(t * m.x_jt[n, t] for t in range(m.est[n], m.lst[n])) - m.act_proc[pre_n]

    return Constraint.Skip

model.precedence_constraint = Constraint(
    model.act_set, model.act_set, rule=activity_precedence_constraint)


# Non preemption constraint for activity n
def no_preemption_constraint(m, n):
    return sum(m.x_jt[n, t] for t in range(m.est[n], m.lst[n])) == 1

model.no_preemption_constraint = Constraint(
    model.act_set, rule=no_preemption_constraint)


# Objective - Minimize finish time of the last activity
def finish_time_objective(m):
    last_activity = value(m.act_count) + 1
    return sum(t * m.x_jt[last_activity, t] for t in range(m.est[last_activity], m.lst[last_activity]))

model.OBJ = Objective(rule=finish_time_objective)
