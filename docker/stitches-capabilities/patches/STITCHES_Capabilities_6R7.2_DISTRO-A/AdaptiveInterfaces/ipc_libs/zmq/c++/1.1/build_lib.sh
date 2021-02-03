#!/bin/bash
#
# Copyright Systems & Technology Research, Apogee Research 2020
# Usage of this software is governed by the LICENSE file accompanying the distribution. 
# By downloading, copying, installing or using the software you agree to this license.
#

FILE=StitchesIPCZmq
rm libstitches_ipc_zmq.a &> /dev/null
g++ -fPIC -O2 -Wall -pedantic -o ./bin/$FILE.o -std=c++11 -c src/$FILE.cpp -I./include -I./../../../CommonAPI/c++/include -isystem -pthread
if [ $? -ne 0 ];
then
  exit 1
fi
pushd ./bin
ar x /usr/local/lib/libzmq.a
if [ $? -ne 0 ];
then
  exit 1
fi
popd
ar rs libstitches_ipc_zmq.a ./bin/*.o 
if [ $? -ne 0 ];
then
  exit 1
fi

exit 0
