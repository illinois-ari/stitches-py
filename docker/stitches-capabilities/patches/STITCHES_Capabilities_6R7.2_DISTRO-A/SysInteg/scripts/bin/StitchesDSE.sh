#! /bin/bash

INTEG_BIN_DIR="$(dirname "$(readlink -f "$0")")"
source ${INTEG_BIN_DIR}/internal/StitchesBuildCommon.sh;

USAGE="$0 [-h] [-v] [-noems] [-dslO(0|1)] [-setmacseed] [-refine] <Build Directory> <SoS Specification> <Inputs Repository> <Output: Configured SoS Spec> <Output: Directory for Configured SS and OCE Specs>"
ARGS=`getopt -q -a -o v,h -l noems,dslO0,dslO1,setmacseed,refine -- "$@"` 
if [ $? -ne 0 ]; then echo $USAGE; exit 1; fi
eval set -- ${ARGS}

# Default Settings
VERBOSITY="&> /dev/null"
REFINE="--refine-sos=false"
DSL_OPT=1

while true; do
    case "$1" in
      "-h" )          echo $USAGE; exit 0;;
      "-v"           ) VERBOSITY="";;
      "--noems"      ) DSE_ARGS+=" --use-ems false";;
      "--setmacseed" ) DSE_ARGS+=" --random-seed=92899664821575";;
      "--dslO0"      ) DSL_OPT=0;;
      "--dslO1"      ) DSL_OPT=1;;
      "--refine"     ) REFINE="--refine-sos=true";;
      "--" ) shift; break;;
      * ) echo $USAGE; exit 1;;
    esac
    shift
done

DSE_ARGS+=" --dsl_opt=$DSL_OPT"
DSE_ARGS+=" $REFINE"

if [ $# -ne 5 ]; then echo $USAGE; exit 1; fi

# Build Directory
BUILD_DIR=$(readlink -f $1)

# SoS Specification
SOS_SPEC_FULL=$(readlink -f $2)
if [ ! -f "$SOS_SPEC_FULL" ]; then error_and_exit "$2 Does Not Exist" 1; fi

# Inputs Repository
INPUTS_DIR=$(readlink -f $3)
if [ ! -d "$INPUTS_DIR" ]; then error_and_exit "$3 Does Not Exist" 1; fi
set_dir_paths $INPUTS_DIR

CONFIGURED_SOS_XML=$4
SS_OCE_DIR=$5

# Make sure the server is running, otherwise exit
#if [ -z $(pgrep -f ftgrepocommserver) ]; then error_and_exit "Community Server Repo Manager not started" 1; fi

########## CREATE BUILD DIR ##########

create_dir $BUILD_DIR
cd $BUILD_DIR

######## CONFIGURE DSE ########

DSE_CONFIG_FILE="dse.config"
cat > $DSE_CONFIG_FILE <<-EOF
SS_SPEC_FILE_DIR        ${SS_SPECS_DIR}
FRAMEWORK_DIR           ${FRAMEWORK_DIR}
OCE_SPEC_FILE_DIR       ${OCE_SPECS_DIR}
LEGACY_SPEC_FILE_DIR    ${LEGACY_SPECS_DIR}
REUSE_ARTIFACT_FILE_DIR ${REUSE_ARTIFACT_DIR}
FTG_HOST                ${FTG_HOST}
EOF

TIME=`pwd`/${TIME_FILE}

######## RUN DSE ########

export LD_LIBRARY_PATH=$DSE_DIR/native/
CMDVAR="$DSE_TOOL --config=${DSE_CONFIG_FILE} --sos-spec=${SOS_SPEC_FULL} --composed-sos=./${CONFIGURED_SOS_XML} --configured-CE-dir=$SS_OCE_DIR ${DSE_ARGS}"
echo $CMDVAR > outCmd.txt
( /usr/bin/time -f "DSE: %U " -a -o ${TIME} $CMDVAR ) 2>&1 | eval "tee -a outCmd.txt ${VERBOSITY}"
ERR=$?
if [ $ERR -ne 0 ]; then error_and_exit "Design Space Exploration Failed ($ERR)" 2; fi
if [ ! -f "${CONFIGURED_SOS_XML}" ] ; then error_and_exit "Design Space Exploration Failed" 3; fi

exit 0
