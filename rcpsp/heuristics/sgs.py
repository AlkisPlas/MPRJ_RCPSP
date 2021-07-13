from pkg_resources import safe_version
import random


def serial_schedule_generation(n, p, preds, r_count, r_cons, r_cap, lft):
    
    eft = {}    
    fin = {}
    scheduled = []

    lst = {act : val - p[act] for act, val in lft.items()}

    fin[0] = 0
    scheduled.append(0)

    for g in range(n + 1):

        eligible_activities = [j for j in range(1, n + 2) if j not in scheduled and set(
            preds[j]) <= set(scheduled)]

        if not eligible_activities:
            print('No feasible schedule could be structured.')
            break

        # Sort eligible activities according to the min LST priority rule
        # sort_asc_lst(eligible_activities, lst)

        while eligible_activities:
            
            j = eligible_activities.pop(0)
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


def sort_asc_lst(eligible_activities, lst):
    n = len(eligible_activities)
    for i in range(n):
        swapped = False
        for j in range(0, n-i-1):
            if lst[eligible_activities[j]] > lst[eligible_activities[j+1]] :
                eligible_activities[j], eligible_activities[j+1] = eligible_activities[j+1], eligible_activities[j]
                swapped = True
        if swapped == False:
            break