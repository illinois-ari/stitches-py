#! /bin/bash

function error() {
    echo "**********************************************************************"
    echo "*********************  ERROR OCCURED !!!! ****************************"
    echo "**********************************************************************"
    echo "$1"
    echo "**********************************************************************"
    exit -1;
}

function dnexit() {
    [ ! -e $1 ] && error "${1} does not exist ... exiting" && exit -1;
}

function usage() {
printf "$0
[-h|--help]

--render-language=Java8
[--gen-orig-fields-and-arrays=<true|false>]
<SS Specification>

--render-language=C++98
[--gen-orig-fields-and-arrays=<true|false>]
<SS Specification>

--render-language=C++11
[--gen-orig-fields-and-arrays=<true|false>]
<SS Specification>

--render-language=C90
[--architecture=<architecture string>]
[--heap-memory-size-kb=<memory in kb>]
<SS Specification>

OR (deprecated):\n\
\n\
$0\n\
<SS Specification>\n\
<C90 | C++98 | C++11 | Java8>\n\
[<OriginalFieldsAndArrays>] (Java8/C++98/C++11 only, not required for them)\n"

}

if [ -z "$STITCHES_CAPABILITIES" ]; then error "STITCHES_CAPABILITIES environment variable not set - did you run BuildCapabilities?"; fi
if [ -z "$STITCHES_LIBRARIES" ]; then error "STITCHES_LIBRARIES environment variable not set - did you run BuildCapabilities?"; fi
if [ -z "$STITCHES_INPUTS" ]; then error "STITCHES_INPUTS environment variable not set - did you run BuildInputs?"; fi


ARGS=`getopt -a -o h -l help,render-language:,architecture:,heap-memory-size-kb:,gen-orig-fields-and-arrays: -- "$@"` 
if [ $? -ne 0 ]; then usage ; exit 2; fi
eval set -- ${ARGS}

GETOPTSUSED=0
if [ "$1" != "--" ];
then
  GETOPTSUSED=1;
fi;

RENDER_LANGUAGE=""
ARCHITECTURE=""
HEAP_MEMORY_SIZE_KB=""
GEN_ORIG_FIELDS_AND_ARRAYS="--gen-orig-fields-and-arrays=false"

while true; do
    case "$1" in
      "-h"|"--help")
        usage;
        shift;
        exit 2;;
      "--render-language" )
        RENDER_LANGUAGE="--render-language=$2";
        shift 2;;
      "--architecture" )
        ARCHITECTURE="--architecture=$2";
        shift 2;;
      "--heap-memory-size-kb" )
        HEAP_MEMORY_SIZE_KB="--heap-memory-size-kb=$2";
        shift 2;;
      "--gen-orig-fields-and-arrays" )
        GEN_ORIG_FIELDS_AND_ARRAYS="--gen-orig-fields-and-arrays=$2";
        shift 2;;
      "--" )
        shift;
        break;;
      * ) 
        usage;
        shift;
        exit 2;;
    esac
done

if [ $# -lt 1 ]; then
  usage; exit -1;
fi
LEGACY_SS_SPEC_XML=$1


# don't allow both getopts and the deprecated calling pattern at the same time
if [ $# -ge 2 ];
then
  if [ $GETOPTSUSED -eq 1 ];
  then
    echo "ERROR: can't mix new and deprecated calling patterns..."; usage; exit -1;
  fi;
fi;

if [ $# -ge 2 ];
then
  RENDER_LANGUAGE="--render-language=$2";
fi

if [ $# -eq 3 ]; then
  ARRAYCHOICE=$3
  if [ "$ARRAYCHOICE" == "OriginalFieldsAndArrays" ]; then
    GEN_ORIG_FIELDS_AND_ARRAYS="--gen-orig-fields-and-arrays=true";
  else
    echo "ERROR: unrecognized choice for array type, use 'OriginalFieldsAndArrays' or nothing"
    usage
    exit -1
  fi
fi


# Validate Spec File
SS_SPEC_FULL=$(cd "$(dirname "$LEGACY_SS_SPEC_XML")"; pwd)/$(basename "$LEGACY_SS_SPEC_XML") && dnexit ${1}
$STITCHES_CAPABILITIES/SysInteg/scripts/ValidateSS.sh $LEGACY_SS_SPEC_XML
if [ $? -ne 0 ]; then
  echo "ERROR validating spec XML"
  exit -1
fi

$STITCHES_CAPABILITIES/AdaptiveInterfaces/ssilintSkeletonGen/genssiskeleton $RENDER_LANGUAGE $ARCHITECTURE $HEAP_MEMORY_SIZE_KB $GEN_ORIG_FIELDS_AND_ARRAYS --delete-sample-upper-impl=true $LEGACY_SS_SPEC_XML
if [ $? -ne 0 ]; then
  echo "ERROR generating LINT skeleton"
  exit -1
fi

exit 0
