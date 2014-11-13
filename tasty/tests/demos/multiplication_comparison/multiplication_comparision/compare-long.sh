#!/bin/sh

ANALYZE=./analyze.py
HE1=../multiplication_homomorphic_onesided/results/1-80-5-long
HE2=../multiplication_homomorphic/results/1-80-5-long
GC1=../multiplication_garbled_onesided/results/1-80-5-long
GC2=../multiplication_garbled/results/1-80-5-long

tasty_post $ANALYZE \
  $HE1/client_costs.bin $HE1/server_costs.bin \
  $HE2/client_costs.bin $HE2/server_costs.bin \
  $GC1/client_costs.bin $GC1/server_costs.bin \
  $GC2/client_costs.bin $GC2/server_costs.bin \

