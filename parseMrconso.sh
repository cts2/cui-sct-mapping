#!/bin/bash
#########################################################
# Run this script before starting the server to parse
# a UMLS MRCONSO.RRF file.
#
# Parameters:
# * Path to UMLS MRCONSO.RRF file (required)
#
# Example: parseMrconso.sh ../my/umls/install/MRCONSO.RRF
#########################################################
echo "Cleaning data directory."
rm -rf data
mkdir data
echo "Starting parse... this may take a few minutes."
awk -F "|" '$12 == "SNOMEDCT" && $17 != "O"' $1 | cut -d "|" -f1,14 | sort | uniq > data/cuiToSnomedCodes.out
echo "Data parse successful."
