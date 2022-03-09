#!/bin/sh
pipreqs . --encoding=utf8 --force
docker build --network=host -t core:4.2.4 .
docker save -o core.tar core:4.2.4