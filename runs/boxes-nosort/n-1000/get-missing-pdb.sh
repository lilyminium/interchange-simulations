#!/bin/bash

NAME="runs-interchange-final"
PDB="ne-2500000_np-1000000_dt-2.0_nb-25.pdb"

find $NAME -mindepth 1 -maxdepth 1 -type d '!' -exec test -e "{}/${PDB}" ';' -print
