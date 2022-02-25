#!/bin/bash

prog="knowledge.py"

function test {
    echo -e "Exécution avec $1 ...\n"
    ./$prog < inputs/$1 > outputs/$1
    echo -e "\nFait.\nexit code: $?"
}

if [ $# -eq 0 ]
then
    for i in $( ls inputs )
    do
        test $i
    done
else
    for i in $*
    do
        cd inputs
        file=$( find $i* )
        cd ..
        test $file
    done
fi
