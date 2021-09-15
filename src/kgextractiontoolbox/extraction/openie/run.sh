#!/bin/bash

cd $1
java -Xms6g -cp "*" edu.stanford.nlp.naturalli.OpenIE -format reverb -output $2 -filelist $3
