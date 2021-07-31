#!/bin/bash

scriptdir=$(dirname "$0")
instancebase=${scriptdir}/../../../data/instances
pk_solverbase=${scriptdir}/../../../rcpsp/formulations/perfect_knowledge
robust_solverbase=${scriptdir}/../../../rcpsp/formulations/robust
resultbase=${instancebase}/../results/

model='continuous'
solver=$(echo $model | cut -c -3)
mkdir -p ${resultbase}/csv

[ -e ${resultbase}/csv/regret.csv ] && rm ${resultbase}/csv/regret.csv
touch ${resultbase}/csv/regret.csv

echo 'instance,true_makespan,worst_case_makespan,regret,gamma' >> ${resultbase}/csv/regret.csv

for indir in ${instancebase}/regret/j30; do
    resdir=$(echo $indir | sed 's:.*/::')
    for infile in ${indir}/*.json; do
        instance=$(echo $infile | sed 's:.*/::' | sed "s/\..*//")
        true_makespan=$(python3 ${pk_solverbase}/${model}/solver_${solver}.py ${resdir} ${instance} -p)
        for gamma in 15 20 25 30
        do
            worst_case_makespan=$(python3 ${robust_solverbase}/${model}/worst_case_makespan/robust_solver_${solver}.py ${resdir} ${instance} -gamma ${gamma} -theta 0.5)
            regret=$(echo "$worst_case_makespan $true_makespan" | awk '{print $1 - $2}')
            retries=0
            while [ $regret -le 0 ] && [ $retries -lt 2 ]
            do
                true_makespan=$(python3 ${pk_solverbase}/${model}/solver_${solver}.py ${resdir} ${instance} -p)
                regret=$(echo "$worst_case_makespan $true_makespan" | awk '{print $1 - $2}')
                retries=$((retries+1))
            done
            printf '%s\n' $instance','$true_makespan','$worst_case_makespan','$regret','$gamma >> ${resultbase}/csv/regret.csv
        done
    done
done
