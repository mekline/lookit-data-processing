#!/bin/bash
# h/t http://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash

while [ $# -gt 0 ]; do
  case "$1" in
    --in=*)
      INPUTDIR="${1#*=}"
      ;;
    --out=*)
      OUTPUTDIR="${1#*=}"
      ;;
    --dbname=*)
      DBNAME="${1#*=}"
      ;;
    *)
      printf "***************************\n"
      printf "* Error: Invalid argument.*\n"
      printf "***************************\n"
      exit 1
  esac
  shift
done

echo "Input mongo dump: ${INPUTDIR}";
echo "Output directory: ${OUTPUTDIR}";
echo "DB name: ${DBNAME}";

eval "mongorestore --drop ${INPUTDIR} && python migrate.py ${INPUTDIR} ${OUTPUTDIR} ${DBNAME}"
