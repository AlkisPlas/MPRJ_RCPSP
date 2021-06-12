from pyomo.environ import *

'''
Mixed-Integer Programming formulation for the RCPSP.
Time horizon is continuous.
'''
model = AbstractModel(name="RCPSP_CONTINUOUS")

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

# Activity processing times
model.act_proc = Param(model.act_set, within=NonNegativeIntegers)

# Activity time windows
model.est = Param(model.act_set, within=NonNegativeIntegers)
model.lst = Param(model.act_set, within=NonNegativeIntegers)
model.eft = Param(model.act_set, within=NonNegativeIntegers)
model.lft = Param(model.act_set, within=NonNegativeIntegers)

# Modelling sets.
model.B = Set(dimen=2)
model.C = Set(dimen=2)
model.G = Set(dimen=2)
model.K = Set(dimen=2)
model.S = Set(dimen=2)
model.P = Set(dimen=2)

# Decision variables.
# Activity start and finishing times.
model.start = Var(model.act_set, within=NonNegativeIntegers)
model.fin = Var(model.act_set, within=NonNegativeIntegers)

'''
Execution sequence variables.

For activities that cannot be executed in parallel x[i,j] = 1 if fin[i] <= start[j], 0 otherwise
For activities that can be executed in parallel x[i,j] = 1 if start[i] <= start[j], 0 otherwise
'''
model.x_set = (model.B | model.G) - model.K
model.x = Var(model.x_set, within=Binary)

'''
Overlapping activity variables

z[i, j] = 1 (i overlaps j) if 
start[i] <= start[j] and fin[i] > start[j]
If i overlaps i then z[i, j] - x[j, i] = 1
'''
model.z = Var(model.P, within=Binary)


# Correlate the finishing and starting time for activities
def start_finish_correlation(m, n):
    return m.fin[n] == m.start[n] + m.act_proc[n]

model.start_finish_correlation_constraint = Constraint(
    model.act_set, rule=start_finish_correlation)


# Constraints for activities with known precedence requirements
def activity_hard_precedence(m, n, pre_n):
    if pre_n in m.act_pre[n]:
        return m.fin[pre_n] <= m.start[n]

    return Constraint.Skip

model.hard_precedence_constraint = Constraint(
    model.act_set, model.act_set, rule=activity_hard_precedence)

''' 
Precedence constraints for activities that can't overlap

If i is scheduled before j (xij = 1 -> xji = 0) then i must finish before j starts (fin[i] <= start[j])
because there are not enough resources for them to overlap. If j is scheduled before i (xji = 1)
then the constraint is skipped because fin[i] - start[j] <= lft[i] - est[j] always holds
'''
def activity_non_overlapping_precedence(m, i, j):
    return m.fin[i] <= m.start[j] + (m.lft[i] - m.est[j]) * m.x[j, i]
        
model.activity_non_overlapping_precedence_constraint = Constraint(
    model.S, rule=activity_non_overlapping_precedence)

'''
Precedence constraints for activities that can overlap

If i is scheduled before j (xij = 1 -> xji = 0) then i must start before j starts (start[i] <= start[j])
as dictated by the decision variables. If j is scheduled before i (xji = 1) then the constraint is skipped 
because start[i] - start[j] <= lst[i] - est[j] always holds
'''
def activity_overlapping_precedence_1(m, i, j):
    if i > j:
        return m.start[j] <= m.start[i] + (m.lst[j] - m.est[i]) * m.x[i, j]

    return Constraint.Skip

model.activity_overlapping_precedence_constraint_1 = Constraint(
    model.P, rule=activity_overlapping_precedence_1)


def activity_overlapping_precedence_2(m, i, j):
    if i > j:
        return m.start[i] + 0.1 <= m.start[j] + (m.lst[i] - m.est[j] + 0.1) * m.x[j, i]

    return Constraint.Skip

model.activity_overlapping_precedence_constraint_2 = Constraint(
    model.P, rule=activity_overlapping_precedence_2)


# For activities without hard precedence constraints, avoid execution cycles.
def no_execution_cycles(m, i, j):
    if i > j and (i, j) not in m.K:
        return m.x[i, j] + m.x[j, i] == 1

    return Constraint.Skip

model.no_execution_cycles_constraint = Constraint(
    model.act_set, model.act_set, rule=no_execution_cycles)

'''
Define overlapping decision variables.
If z[i, j] is 0 then i and j are not overlapping meaning that i finishes before j starts.
If z[i, j] is 1 then the constraint is skipped because fin[i] - start[j] <= lft[i] - est[j] always holds
'''
def overlapping_variables(m, i, j):
    return m.fin[i] <= m.start[j] + (m.lft[i] - m.est[j]) * m.z[i, j]

model.overlapping_variables_constraint = Constraint(
    model.P, rule=overlapping_variables)


# Resource capacity constraint for resource r
def resource_capacity_constraint(m, i, k):
    return m.r_cons[i, k] + sum(m.r_cons[j, k] * (m.z[j, a] - m.x[a, j]) for a, j in m.P if i == a) <= m.r_cap[k]

model.resource_constraint = Constraint(
    model.act_set, model.r_set, rule=resource_capacity_constraint)

'''
For activities that can be executed in parallel,
if i starts before j then j must be overlapping i.
'''
def tighten_decision_variables(m, i, j):
    return m.x[i, j] <= m.z[j, i]

model.tighten_decision_variables_constraint = Constraint(
    model.P, rule=tighten_decision_variables)


def preprocessing_phase_relaxation(m, i, j):
    if i != j and m.lst[i] <= m.est[j]:
        return m.x[i, j] == 1

    return Constraint.Skip

model.preprocessing_phase_relaxation_constraint = Constraint(
    model.P, rule=preprocessing_phase_relaxation)


# Minimize finish time of the last activity
def finish_time_objective(m):
    return m.fin[value(m.act_count) + 1]

model.OBJ = Objective(rule=finish_time_objective)
