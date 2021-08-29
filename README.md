# MPRJ_RCPSP

Formulations for the robust Resource-Constrained Project Scheduling Problem (RCPSP) using Pyomo modelling.

The project is structured as follows.

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
