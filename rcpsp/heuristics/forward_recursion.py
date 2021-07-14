def get_earliest_times(n, act_pre, act_proc):
    est = {}
    for act in range(n):
        est[act] = max((est[pre] + act_proc[pre]
                    for pre in act_pre[act]), default=0)
    eft = {act : val + act_proc[act] for act, val in est.items()}
    return est, eft