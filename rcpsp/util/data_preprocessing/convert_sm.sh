#!/bin/bash

SCRIPTDIR=$(dirname "$0")
INSTANCEBASE=${SCRIPTDIR}/../../../data/instances

for INDIR in ${INSTANCEBASE}/sm/*; do
    for INFILE in ${INDIR}/*.sm; do
        python3 ${SCRIPTDIR}/psplibconverter.py ${INFILE}
    done
done
