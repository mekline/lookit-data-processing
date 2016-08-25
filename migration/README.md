# Instructions

### Setup

This directory contains code to migrate accounts from the old database schema to the new one. To run this code you need to:

- have a copy of the mongobackup from the database you want to migrate, and know it's path
- have mongodb installed and running
- have python 2.7.X installed, preferably using a [virtualenv](https://virtualenv.pypa.io/en/latest/) to isolate this project's dependencies
- install the python requirements: `pip install -r requirements.txt`

### Running

`./migrate.sh --in=<PATH_TO_MONGODUMP> --out=./output --dbname=users`

which creates an accounts.json file in the output directory.
