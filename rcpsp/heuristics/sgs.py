from pkg_resources import safe_version
import random

def serial_schedule_generation(inst):

    eft = inst['eft']
    lft = inst['lft']
    n = inst['act_count']
    p = inst['act_proc']
    preds = inst['act_pre']
    r_count = inst['r_count']
    r_cons = inst['r_cons']
    r_cap = inst['r_cap']

    fin = {}
    scheduled = []

    fin[0] = 0
    scheduled.append(0)

    for g in range(1, n + 2):

        eligible_activities = [j for j in range(1, n + 2) if j not in scheduled and set(
            preds[j]) <= set(scheduled)]
        print('\nEligible at stage {g} are {eligible}'.format(g=g, eligible=eligible_activities))

        if not eligible_activities:
            print('No feasible schedule could be structured.')
            break

        while eligible_activities:
            
            j = random.choice(eligible_activities)
            eligible_activities.remove(j)

            eft[j] = max((fin[pre] for pre in preds[j]), default=0) + p[j]
            print('\nScheduling {j} with est={est} and lst={lst}'.format(j=j,est=eft[j]-p[j],lst=lft[j] - p[j]))

            eligible_times = []
            for t in range(eft[j] - p[j], lft[j] - p[j] + 1):
                if t in fin.values():               
                    active = get_active_jobs(t, scheduled, fin, p)
                    for k in range(1, r_count + 1):
                        if r_cons[j, k] <= r_cap[k] - sum(r_cons[act_j, k] for act_j in active):
                            eligible_times.append(t)
                        else:
                            print('No units of resource {k} available at {t}'.format(k=k, t=t))

            print('Eligible times ', eligible_times)
            if eligible_times:
                fin[j] = min(eligible_times) + p[j]
                print('adding {act}, starting at {start} finishing at {fin}'.format(
                    act=j, start=fin[j]-p[j], fin=fin[j]))

                scheduled.append(j)
                break

    return fin[n]


def get_active_jobs(t, scheduled, fin, p):
    active = [s for s in scheduled if fin[s] > t and fin[s] - p[s] <= t]
    print('Active at time {time}: {active}'.format(time=t, active=active))
    return active
