class BackwardRecursion:
 
    def __init__(self, n, upper_bound, act_pre, act_proc):
        self.act_pre = act_pre
        self.act_proc = act_proc
        self.n = n
        self.lst = {}
        self.lst[n] = upper_bound
        self.lft = {}
        self.visited = []
    
    def __get_latest_starting_time(self, act):
        for pre in self.act_pre[act]:
            if pre not in self.visited:
                self.visited.append(pre)
                self.lst[pre] = self.lst[act] - self.act_proc[pre]
                self.__get_latest_starting_time(pre)

    def get_latest_times(self):
        self.__get_latest_starting_time(self.n)
        self.lft = {act : val + self.act_proc[act] for act, val in self.lst.items()}
        return self.lst, self.lft