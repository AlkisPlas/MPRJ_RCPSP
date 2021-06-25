from pkg_resources import safe_version
import random


def serial_schedule_generation(n, p, preds, r_count, r_cons, r_cap, lft):
    
    eft = {}    
    fin = {}
    scheduled = []

    fin[0] = 0
    scheduled.append(0)

    for g in range(n + 1):

        eligible_activities = [j for j in range(1, n + 2) if j not in scheduled and set(
            preds[j]) <= set(scheduled)]

        if not eligible_activities:
            print('No feasible schedule could be structured.')
            break

        while eligible_activities:

            j = random.choice(eligible_activities)
            eligible_activities.remove(j)

            eft[j] = max((fin[pre] for pre in preds[j]), default=0) + p[j]

            eligible_times = []
            for t in range(eft[j] - p[j], lft[j] - p[j] + 1):
                if t in fin.values():
                    is_eligible = True
                    for k in range(1, r_count + 1):
                        for moment in range(t, t + p[j] + 1):
                            active = get_active_jobs(moment, scheduled, fin, p)
                            if r_cons[j, k] > r_cap[k] - sum(r_cons[act_j, k] for act_j in active):
                                is_eligible = False
                                break

                    if is_eligible:
                        eligible_times.append(t)

            if eligible_times:
                fin[j] = min(eligible_times) + p[j]
                scheduled.append(j)
                break

    return fin[n + 1]


def get_active_jobs(t, scheduled, fin, p):
    return [s for s in scheduled if fin[s] > t and fin[s] - p[s] <= t]