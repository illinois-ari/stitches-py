#!/bin/bash
#
# Copyright Systems & Technology Research, Apogee Research 2020
# Usage of this software is governed by the LICENSE file accompanying the distribution. 
# By downloading, copying, installing or using the software you agree to this license.
#

DEFS=""
# If system does not support ntohl, htonl, the library will implement its own based upon STITCHES_HOST_BIG_ENDIAN
#DEFS=${DEFS}" -DSTITCHES_IPC_NO_ENDIAN_MACROS"
#DEFS=${DEFS}" -DSTITCHES_HOST_ENDIAN_BIG"

FILE=StitchesIPCTCP
rm libstitches_ipc_tcp.a &> /dev/null
g++ -fPIC $DEFS -O2 -Wall -pedantic -o ./bin/$FILE.o -std=c++98 -c src/$FILE.cpp -I./include -I./../../../CommonAPI/c++/include -pthread
if [ $? -ne 0 ];
then
  exit 1
fi
ar rs libstitches_ipc_tcp.a ./bin/*.o 
if [ $? -ne 0 ];
then
  exit 1
fi

exit 0
