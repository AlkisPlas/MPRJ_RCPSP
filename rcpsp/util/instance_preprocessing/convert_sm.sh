#!/bin/bash

scriptdir=$(dirname "$0")
instancebase=${scriptdir}/../../../data/instances

for indir in ${instancebase}/sm/*; do
    for infile in ${indir}/*.sm; do
        python3 ${scriptdir}/psplibconverter.py ${infile}
    done
done
