#!/bin/bash

cd wikipedia/
bash wikipedia_scripts.sh
cd ../

cd pubmed/
bash pubmed_scripts.sh
cd ../

cd pollux/
bash pollux_scripts.sh
cd ../

cd corenlp/
bash all.sh
cd ../

cd canonicalization_advanced/
bash all.sh
cd ../

cd multilingual/
bash all.sh
cd ../