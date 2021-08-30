#!/bin/bash

scriptdir=$(dirname "$0")
instancebase=${scriptdir}/../../../data/instances
solverbase=${scriptdir}/../../../rcpsp/formulations/perfect_knowledge
resultbase=${instancebase}/../results

model='continuous'
solver=$(echo $model | cut -c -3)
mkdir -p ${resultbase}/csv

[ -e ${resultbase}/csv/pr_random.csv ] && rm ${resultbase}/csv/pr_random.csv
touch ${resultbase}/csv/pr_random.csv

echo 'instance,min_lft' >> ${resultbase}/csv/pr_random.csv

for indir in ${instancebase}/json/*; do
    resdir=$(echo $indir | sed 's:.*/::')
    for infile in ${indir}/*.json; do
        instance=$(echo $infile | sed 's:.*/::' | sed "s/\..*//")
        pop_first=$(python3 ${scriptdir}/run_sgs.py ${resdir} ${instance})
        #min_lft=$(python3 ${scriptdir}/run_sgs.py ${resdir} ${instance} -pr)
        #printf '%s\n' $instance','$pop_first','$min_lst >> ${resultbase}/csv/pr.csv
        printf '%s\n' $instance','$pop_first >> ${resultbase}/csv/pr_random.csv
    done
done
