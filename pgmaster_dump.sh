#! /bin/bash

echo "INFO: this is a pgmaster-database dump program."

cd "$(dirname "$0")"

# read environment
if [ -e environment ];
then
    . `pwd`/environment
else
    echo "ERROR: environment does not found"
    exit 1
fi

echo -n "INFO: connection test...."
mes=`psql -l 2>&1`
if [ $? -eq  0 ];
then
    echo "OK"
else
    echo "NG"
    echo ${mes}
    exit 1
fi

suffix=`date +%Y%m%d_%H`
filename=pgmaster_dump_${suffix}.bak

if [ -e ${filename} ];
then
    echo "ERROR: ${filename} already exists."
    exit 1
fi

echo -n "INFO: dump is working..."
mes=`pg_dump -Fc -f ${filename} 2>&1`
if [ $? -eq 0 ];
then
    echo "OK"
else
    echo "NG"
    echo "ERROR: ${mes}"
    exit 1
fi

echo "LOG: dump has completed."
echo "LOG: filename: ${filename}"
echo "LOG: `ls -l ${filename}`"

exit 0
