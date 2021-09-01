## Mixed integer programming formulations for the robust resource constrained project scheduling problem. ##

This project investigates the impact of different formulations on the solution quality of the robust resource constraint project scheduling problem (RCPSP). 

Two mixed-integer programming (MIP) formulations are presented under the assumption of deterministic activity processing times. These are found under the ```rcpsp/formulations/perfect_knowledge``` directory. <br/>```rcpsp_dis.py``` separates the time horizon to discrete intervals while ```rcpsp_con.py``` assumes a continuous horizon .

Following a minimax bilevel approach, we formulate the worst case makespan robust RCPSP using the pyomo.bilevel package. The bilevel models are reformulated to each of the perfect-knowledge MIP formulations  and then solved using the CPLEX solver. These can be found under the ```rcpsp/formulations/robust``` directory.

For every formulation we implement a pyomo abstract model and a corresponding solver class that instantiates the model, computes a warm start solution using a serial schedule generation scheme ```rcpsp/heuristics/sgs.py``` and invokes CPLEX using the SolverFactory wrapper.

The models are executed on the PSPLIB instances found under ```data/instances/json```.


The project is structured as follows.

```bash
.
├── README.md
├── data
│   └── instances
│       ├── json
│       │   ├── j120
│       │   ├── j30
│       │   ├── j60
│       │   └── j90
│       └── sm
│           ├── j120
│           ├── j30
│           ├── j60
│           └── j90
└── rcpsp
    ├── formulations
    │   ├── perfect_knowledge
    │   │   ├── continuous
    │   │   │   ├── rcpsp_con.py
    │   │   │   └── solver_con.py
    │   │   └── discrete
    │   │       ├── rcpsp_dis.py
    │   │       └── solver_dis.py
    │   └── robust
    │       ├── continuous
    │       │   └── worst_case_makespan
    │       │       ├── robust_rcpsp_con.py
    │       │       └── robust_solver_con.py
    │       └── discrete
    │           └── worst_case_makespan
    │               ├── robust_rcpsp_dis.py
    │               └── robust_solver_dis.py
    ├── heuristics
    │   ├── backward_recursion.py
    │   ├── forward_recursion.py
    │   └── sgs.py
    └── util
        ├── instance_execution
        │   ├── run_instances.sh
        │   └── worst_case_regret.sh
        ├── instance_postprocessing
        │   └── process_instance_results_extract_csv.py
        ├── instance_preprocessing
        │   ├── convert_sm.sh
        │   └── psplibconverter.py
        └── priority_rule_evaluation
            ├── run_pr.sh
            └── run_sgs.py
```
