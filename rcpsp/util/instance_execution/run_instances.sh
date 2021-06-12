#!/bin/bash

scriptdir=$(dirname "$0")
instancebase=${scriptdir}/../../../data/instances
solverbase=${scriptdir}/../../../rcpsp/formulations/perfect_knowledge

for indir in ${instancebase}/json/*; do
    for infile in ${indir}/*.json; do
        instance=$(echo $infile | sed 's:.*/::' | sed "s/\..*//")
        indir=$(echo $indir | sed 's:.*/::')
        python3 ${solverbase}/discrete/solver_dis.py ${indir} ${instance}
    done
done
