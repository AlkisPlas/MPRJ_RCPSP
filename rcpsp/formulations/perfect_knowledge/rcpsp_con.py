from pyomo.environ import *

'''
Mixed-Integer Programming formulation for the RCPSP.
Time horizon is continuous.
'''
model = AbstractModel(name = "RCPSP_CONTINUOUS")

#Activity set
model.act_count = Param(within=NonNegativeIntegers, mutable=True)
model.act_set = RangeSet(0, model.act_count + 1)

#Activity Precedence Set
model.act_pre = Param(model.act_set, mutable=True, domain=Any)

#Resource set
model.r_count = Param(within=NonNegativeIntegers, domain=Any)
model.r_set = RangeSet(model.r_count)

#Available units of all resources 
model.r_cap = Param(model.r_set)

#Resource consumption of activities
model.r_cons = Param(model.act_set, model.r_set, within=NonNegativeReals, mutable=True)

#Activity processing times
model.act_proc = Param(model.act_set, within=NonNegativeReals)

#Decision variables. 
#Activity start and finishing times.
model.s_i = Var(model.act_set, within=Reals, initialize=False)
model.f_i = Var(model.act_set, within=NonNegativeReals, initialize=0.0)

#Execution sequence. If activity i is starts before j (s_i < s_j)
model.x_ij = Var(model.act_set, model.act_set, within=Binary, initialize=False)


#Resource capacity constraint for resource r
def resource_capacity_constraint(m, r):
    return sum(m.r_cons[act, r] for act in m.act_set) <= m.r_cap[r]

model.resource_constraint = Constraint(model.r_set, rule=resource_capacity_constraint)

#Precedence constraint for activity n
def activity_precedence_constraints(m, n, pre_n):
    if n == 0:
        return Constraint.Skip

    if pre_n in value(m.act_pre[n]):
        return m.f_i[pre_n] <= m.f_i[n] - m.act_proc[n]

    return Constraint.Skip

model.precedence_constraint = Constraint(model.act_set, model.act_set, rule=activity_precedence_constraints)

def finish_time_objective(m):
    return m.f_i[value(m.act_count) + 1]

#Minimize finish time of the last activity
model.OBJ = Objective(rule=finish_time_objective)