#!/bin/sh

ANALYZE=./analyze.py
DIR=
HE1=../multiplication_homomorphic_onesided/results/$DIR
HE2=../multiplication_homomorphic/results/$DIR
GC1=../multiplication_garbled_onesided/results/$DIR
GC2=../multiplication_garbled/results/$DIR

tasty_post $ANALYZE \
  $HE1/costs.bin \
  $HE2/costs.bin \
  $GC1/costs.bin \
  $GC2/costs.bin

