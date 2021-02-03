#!/bin/bash
#
# Copyright Systems & Technology Research, Apogee Research 2020
# Usage of this software is governed by the LICENSE file accompanying the distribution. 
# By downloading, copying, installing or using the software you agree to this license.
#

if [ -z "$STITCHES_LIBRARIES" ]; then error "STITCHES_LIBRARIES environment variable not set"; fi

ln -f -s $STITCHES_LIBRARIES/libs/SoSBuildTemplate/vendor .

function build_lib() {
  local LIBDIR="$1"
  printf "build IPC library in $LIBDIR..."
  pushd $LIBDIR >& /dev/null
  ./build_lib.sh >& build_lib.txt
  THIS_SUCCESS=$?
  if [ $THIS_SUCCESS -eq 0 ];
  then
    printf "\x1B[1;32mPASS\x1B[0m\n"
    popd >& /dev/null
    return 0
  else
    printf "\x1B[0;31mFAIL\x1B[0m\n"
    echo "Errors logged to $PWD/build_lib.txt"
    popd >& /dev/null
    return 1
  fi
}

SUCCESS=0
declare -a LIBDIRS=("posix_mqueue/c++/1.0/" \
                    "posix_mqueue/c++/1.1/" \
                    "posix_mqueue/c90/1.0/" \
                    "posix_mqueue/c90/1.1/" \
                    "posix_named_pipe/c++/1.0/" \
                    "posix_named_pipe/c++/1.1/" \
                    "posix_named_pipe/c90/1.0/" \
                    "posix_named_pipe/c90/1.1/" \
                    "posix_named_pipe/java/1.0/" \
                    "tcp/c++/1.0/" \
                    "tcp/c++/1.1/" \
                    "tcp/c90/1.1/" \
                    "zmq/c++/1.0/" \
                    "zmq/c++/1.1/" \
                    "zmq/java/1.0/" \
                    "zmq/java/1.1/")


for LIBDIR_I in "${LIBDIRS[@]}"
do
  build_lib $LIBDIR_I
  if [ $? -ne 0 ];
  then
    SUCCESS=1
  fi
done

if [ $SUCCESS -eq 0 ];
then
  echo -e "\x1B[1;32mSUCCESS\x1B[0m building IPC libraries"
else
  echo -e "\x1B[0;31mFAIL\x1B[0m building one or more IPC libraries"
fi

exit $SUCCESS
