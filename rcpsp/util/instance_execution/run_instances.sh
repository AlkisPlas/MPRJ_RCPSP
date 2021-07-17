#!/bin/bash

export PYTHONPATH="${PYTHONPATH}:/Users/alplas/kings/dissertation/MPRJ_RCPSP"

scriptdir=$(dirname "$0")
instancebase=${scriptdir}/../../../data/instances
solverbase=${scriptdir}/../../../rcpsp/formulations/perfect_knowledge
resultbase=${instancebase}/../results

model='continuous'
solver=$(echo $model | cut -c -3)

for indir in ${instancebase}/json/*; do
    resdir=$(echo $indir | sed 's:.*/::')
    mkdir -p ${resultbase}/${model}/${resdir}
    for infile in ${indir}/*.json; do
        instance=$(echo $infile | sed 's:.*/::' | sed "s/\..*//")
        python3 ${solverbase}/${model}/solver_${solver}.py ${resdir} ${instance}
    done
done
