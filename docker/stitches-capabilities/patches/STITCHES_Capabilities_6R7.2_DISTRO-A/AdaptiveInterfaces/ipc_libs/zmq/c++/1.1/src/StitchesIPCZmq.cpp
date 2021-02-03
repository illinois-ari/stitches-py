/*
 * Copyright Systems & Technology Research, Apogee Research 2020
 * Usage of this software is governed by the LICENSE file accompanying the distribution. 
 * By downloading, copying, installing or using the software you agree to this license.
 */

#include <string>
#include <cstring>
#include <zmq.h>
#include "StitchesIPCZmq.h"

#include "spdlog/spdlog.h"

namespace Stitches {

StitchesIPCZmq::StitchesIPCZmq()
 : StitchesIPC(),
   requestBuf( NULL ),
   returnBuf( NULL ),
   configTransmit( NULL ),
   configReceive( NULL ),
   errorString( "General Error" ),
   zmqContext( NULL ),
   zmqSocket( NULL )
{
}

int StitchesIPCZmq::initTransmit(const char **configString, void (*_returnBuf)(unsigned char *buf)) {
    if(configString == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    if(zmqContext != NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    zmqContext = zmq_ctx_new();
    if(zmqContext == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    configTransmit = (char **)configString;
    configReceive  = NULL;
    returnBuf      = _returnBuf;

    return STITCHES_IPC_RC_OK;
}

int StitchesIPCZmq::initReceive(const char **configString, unsigned char *(*_requestBuf)(size_t size)) {
    if(configString == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    if(zmqContext != NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    zmqContext = zmq_ctx_new();
    if(zmqContext == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    configReceive = (char **)configString;
    configTransmit = NULL;
    requestBuf    = _requestBuf;

    return STITCHES_IPC_RC_OK;
}

int StitchesIPCZmq::open() {
    if((zmqContext == NULL) || (zmqSocket != NULL)) return STITCHES_IPC_RC_ERROR_SEVERE;
   
    zmqSocket = zmq_socket(zmqContext, ZMQ_PAIR);
    if(zmqSocket == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    int linger = 0;
    zmq_setsockopt(zmqSocket, ZMQ_LINGER, &linger, sizeof(linger));

    if(configReceive != NULL) {
        if(lookupAddr(configReceive) != STITCHES_IPC_RC_OK) return STITCHES_IPC_RC_ERROR_SEVERE;
        spdlog::info("Binding to address {}", addr);
        int err = zmq_bind(zmqSocket, addr);
        if (err !=0) {
            spdlog::error("ZMQ error {}", zmq_strerror(err));
            close();
            return STITCHES_IPC_RC_RETRY;
        }

    } else if(configTransmit != NULL) {
        if(lookupAddr(configTransmit) != STITCHES_IPC_RC_OK) return STITCHES_IPC_RC_ERROR_SEVERE;
        spdlog::info("Connecting to address {}", addr);
        int err = zmq_connect(zmqSocket, addr);
        if (err !=0) {
            spdlog::error("ZMQ error {}", zmq_strerror(err));
            close();
            return STITCHES_IPC_RC_RETRY;
        }
    } else {
        close();
        return STITCHES_IPC_RC_ERROR_SEVERE;
    }

    return STITCHES_IPC_RC_OK;
}

int StitchesIPCZmq::close() {
    if(zmqSocket == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;
    zmq_close(zmqSocket);
    zmqSocket = NULL;
    return STITCHES_IPC_RC_OK;
}

int StitchesIPCZmq::read(unsigned char **buf, size_t *length) {
    if(zmqSocket == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;
    if(buf == NULL)       return STITCHES_IPC_RC_ERROR_SEVERE;
    if(length == NULL)    return STITCHES_IPC_RC_ERROR_SEVERE;

    zmq_msg_t msg;

    if(zmq_msg_init(&msg) != 0) {
        return STITCHES_IPC_RC_ERROR_OTHER;
    }

    if(zmq_msg_recv(&msg, zmqSocket, 0) == -1) {
        zmq_msg_close(&msg);
        return STITCHES_IPC_RC_TERM;
    }

    *length = zmq_msg_size(&msg);

    // Request Buffer from HCAL
    *buf = requestBuf(*length);

    if(*buf == (void *)0) {
        *length = 0;
        zmq_msg_close(&msg);
        return STITCHES_IPC_RC_ERROR_OUT_OF_BUF;
    }

    std::memcpy(*buf, (const char *)zmq_msg_data(&msg), *length);
 
    zmq_msg_close(&msg);
 
    return STITCHES_IPC_RC_OK;
}

int StitchesIPCZmq::term() {
    if((zmqContext == NULL)) return STITCHES_IPC_RC_ERROR_SEVERE;
    zmq_ctx_shutdown(zmqContext);
    zmq_ctx_term(zmqContext);
    zmqContext = NULL;
    return STITCHES_IPC_RC_OK;
}

int StitchesIPCZmq::write(const unsigned char *buf, size_t length) {
    if(zmqSocket == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;
    if(buf == NULL)       return STITCHES_IPC_RC_ERROR_SEVERE;

    // Blocking Send
    if(zmq_send(zmqSocket, buf, length, ZMQ_NOBLOCK)) {
        // Note: error code (EAGAIN) does not distinguish between message buffered due to missing connection
        // and message dropped due to buffer full condition
        int err = zmq_errno();
        if(err != EAGAIN) {
            // Don't invoke Return Buffer - HCAL keeps buffer upon errors
            return (err == ETERM) ? STITCHES_IPC_RC_TERM : STITCHES_IPC_RC_ERROR_SEVERE;
        }
    }

    // Return Buffer to HCAL
    returnBuf((unsigned char *)buf);
    return STITCHES_IPC_RC_OK;
}
 
int StitchesIPCZmq::lookupAddr(char **s) {
    if(s[0] == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    memset(addr, 0, sizeof(addr)); 
    strcpy(addr, "tcp://");

    if(strcmp(s[0], "")) {
        // Metadata File
        FILE *f = ::fopen(s[0], "r");
        if(f == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;
        char *s = fgets(&addr[strlen(addr)], 16, f);
        if(s == NULL) { fclose(f); return STITCHES_IPC_RC_ERROR_SEVERE; }
        while((strlen(addr) > 0) && ((addr[strlen(addr)-1] == 10) || addr[strlen(addr)-1] == 13)) {
            addr[strlen(addr) - 1] = 0;
        }
        strcpy(&addr[strlen(addr)], ":");
        s = fgets(&addr[strlen(addr)], 6, f);
        if(s == NULL) { fclose(f); return STITCHES_IPC_RC_ERROR_SEVERE; }
        while((strlen(addr) > 0) && ((addr[strlen(addr)-1] == 10) || addr[strlen(addr)-1] == 13)) {
            addr[strlen(addr) - 1] = 0;
        }
        fclose(f);
    } else {
        if((s[1] == NULL) || (s[2] == NULL)) return STITCHES_IPC_RC_ERROR_SEVERE;
        strncpy(&addr[strlen(addr)], s[1], 16);
        strcpy(&addr[strlen(addr)], ":");
        strncpy(&addr[strlen(addr)], s[2], 6);
    } 

    return STITCHES_IPC_RC_OK;
}
 
char* StitchesIPCZmq::getLastError() {
    return (char *)errorString;
}

}
