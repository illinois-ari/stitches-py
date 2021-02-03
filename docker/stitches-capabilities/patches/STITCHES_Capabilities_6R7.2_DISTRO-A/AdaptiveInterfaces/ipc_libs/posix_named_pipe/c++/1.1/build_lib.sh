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

FILE=StitchesIPCPosixNamedPipe
rm libstitches_ipc_posix_named_pipe.a &> /dev/null
g++ -fPIC $DEFS -O2 -std=c++11 -Wall -pedantic -o ./bin/$FILE.o -c src/$FILE.cpp -I./include -I./../../../CommonAPI/c++/include 
if [ $? -ne 0 ];
then
  exit 1
fi
ar rs libstitches_ipc_posix_named_pipe.a ./bin/*.o 
if [ $? -ne 0 ];
then
  exit 1
fi

exit 0
