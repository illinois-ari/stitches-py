/*
 * Copyright Systems & Technology Research, Apogee Research 2020
 * Usage of this software is governed by the LICENSE file accompanying the distribution. 
 * By downloading, copying, installing or using the software you agree to this license.
 */

#include "StitchesIPCPosixNamedPipe.h"
#include <string>
#include <errno.h>
#include <arpa/inet.h>
#include <sys/eventfd.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <iostream>

#include "spdlog/spdlog.h"

#ifdef STITCHES_IPC_NO_ENDIAN_MACROS
  #undef ntohl
  #undef htonl
  #ifdef STICHES_HOST_ENDIAN_BIG
    #define ntohl(val) (val)
    #define htonl(val) (val)
  #else
    #define ntohl(val) (\
      ((((val) >> 0)  & 0xFF) << 24) |\
      ((((val) >> 8)  & 0xFF) << 16) |\
      ((((val) >> 16) & 0xFF) << 8) |\
      ((((val) >> 24) & 0xFF) << 0) )
    #define htonl(val) ntohl(val)
  #endif
#endif

namespace Stitches {

StitchesIPCPosixNamedPipe::StitchesIPCPosixNamedPipe()
 : StitchesIPC(),
    requestBuf( NULL ),
    returnBuf( NULL ),
    configTransmit( NULL ),
    configReceive( NULL ),
   errorString( "General Error" ),
   fd( -1 ),
   fd_stop(  -1 )
{
}

int StitchesIPCPosixNamedPipe::initTransmit(const char **configString, void (*_returnBuf)(unsigned char *buf)) {
    if(configString == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;
    if(fd != -1) return STITCHES_IPC_RC_ERROR_SEVERE;

    configTransmit = (char **)configString;
    configReceive  = NULL;
    returnBuf      = _returnBuf;

    return STITCHES_IPC_RC_OK;
}

int StitchesIPCPosixNamedPipe::initReceive(const char **configString, unsigned char *(*_requestBuf)(size_t size)) {
    if(configString == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;
    if(fd != -1) return STITCHES_IPC_RC_ERROR_SEVERE;

    configReceive  = (char **)configString;
    configTransmit = NULL;
    requestBuf     = _requestBuf;

    return STITCHES_IPC_RC_OK;
}

int StitchesIPCPosixNamedPipe::open() {
    spdlog::debug("Starting open named pipe");
    if(fd != -1){
        return STITCHES_IPC_RC_ERROR_SEVERE;
    }
   
    if(configReceive != NULL) {
        if(lookupPipe(configReceive) != STITCHES_IPC_RC_OK) {
            spdlog::error("lookPipe failed");
            return STITCHES_IPC_RC_ERROR_SEVERE; 
        }
        spdlog::info("Opening pipe {} for reading", pipeName);
        fd = ::open(pipeName, O_RDONLY );

        if (fd == -1) {
            spdlog::error("Error opening pipe {} for reading", pipeName);
            //spdlog::error(std::strerror(errorno));
            return STITCHES_IPC_RC_RETRY;
        }
        fd_stop = eventfd(0, 0);
    } else if(configTransmit != NULL) {
        try {
            if(lookupPipe(configTransmit) != STITCHES_IPC_RC_OK) {
                spdlog::error("lookPipe failed");
                return STITCHES_IPC_RC_ERROR_SEVERE;
            }
            spdlog::info("Creating pipe {} for writing", pipeName);
            int mkFifoRet = ::mkfifo(pipeName, 0640);
            if(mkFifoRet != 0) {
                spdlog::error("mkfifo failed with code {}", mkFifoRet);
                return STITCHES_IPC_RC_ERROR_SEVERE;
            }

            // Set blocking mode
            
            int flags = fcntl(fd, F_GETFL, 0) | O_NONBLOCK;
            spdlog::info("Setting block mode {}", flags);
            fcntl(fd, F_SETFL, flags);
            spdlog::info("Opening named pipe");
            fd = ::open(pipeName, O_WRONLY );

            // Unless another signal handler is installed, ignore SIGPIPE caused by peer closing pipe
            struct sigaction query_action;
            if (!sigaction (SIGINT, NULL, &query_action) &&
                ((query_action.sa_handler == SIG_DFL) || (query_action.sa_handler == SIG_IGN)))
            {
                signal(SIGPIPE, SIG_IGN);
            }
        } catch( std::exception& e) {

            return STITCHES_IPC_RC_ERROR_SEVERE;
        }

    }
    std::cout << "End of open" << std::endl;

    return STITCHES_IPC_RC_OK;
}

int StitchesIPCPosixNamedPipe::close() {
    if(fd == -1) return STITCHES_IPC_RC_ERROR_SEVERE;
    
    ::close(fd);

    if(configTransmit != NULL) {
        // Delete named pipe
        if(::unlink(pipeName) != 0) return STITCHES_IPC_RC_ERROR_SEVERE;
    }

    fd = -1;
    fd_stop = -1;

    return STITCHES_IPC_RC_OK;
}

int StitchesIPCPosixNamedPipe::read(unsigned char **buf, size_t *length) {
    if(fd == -1)       return STITCHES_IPC_RC_ERROR_SEVERE;
    if(buf == NULL)    return STITCHES_IPC_RC_ERROR_SEVERE;
    if(length == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;

    // Wait for data
    FD_ZERO(&read_fds);
    FD_SET(fd, &read_fds);
    FD_SET(fd_stop, &read_fds);
    int max = (fd > fd_stop) ? fd : fd_stop;
    select(max + 1, &read_fds, NULL, NULL, NULL);
    if(FD_ISSET(fd_stop, &read_fds)) {
        // Term signaled read to stop
        return STITCHES_IPC_RC_TERM;
    }

    // Read Size Framing
    uint32_t size;
    int rc;

    if((rc = readBytes(fd, (void *)&size, sizeof(uint32_t))) != STITCHES_IPC_RC_OK) return rc;
    *length = ntohl(size);

    // Request Buffer from HCAL
    *buf = requestBuf(*length);

    if(*buf == (void *)0) {
        // Read and discard message
        unsigned char ch;
        while((*length)--) {
            if((rc = readBytes(fd, (void *)&ch, sizeof(unsigned char))) != STITCHES_IPC_RC_OK) return rc;
        }
        return STITCHES_IPC_RC_ERROR_OUT_OF_BUF;
    }

    // Read the actual message
    return readBytes(fd, (void *)(*buf), *length);
}

int StitchesIPCPosixNamedPipe::write(const unsigned char *buf, size_t length) {
    if(fd == -1)    return STITCHES_IPC_RC_ERROR_SEVERE;
    if(buf == NULL) return STITCHES_IPC_RC_ERROR_SEVERE;
   
    // Frame as Length, Data
    uint32_t lfield = htonl((uint32_t)length);

    int rc;
    if((rc = writeBytes(fd, (void *)&lfield, sizeof(uint32_t))) != STITCHES_IPC_RC_OK) return rc;
    if((rc = writeBytes(fd, (void *)buf, length)) != STITCHES_IPC_RC_OK) return rc;

    // Return Buffer to HCAL
    returnBuf((unsigned char *)buf);
    return STITCHES_IPC_RC_OK;
}

int StitchesIPCPosixNamedPipe::term() {
    uint64_t val = 1;
           
    // TBD : Can't terminate writer

    if(fd_stop != -1) {
        // Signal blocked read to unblock
        ::write(fd_stop, &val, sizeof(val));
    }

    return STITCHES_IPC_RC_OK;
}

char* StitchesIPCPosixNamedPipe::getLastError() {
    return (char *)errorString;
}

int StitchesIPCPosixNamedPipe::lookupPipe(char **s) {
    if(s[0] == NULL) {
        return STITCHES_IPC_RC_ERROR_SEVERE;
    }

    spdlog::info("Looking up pipeName in config {}", s[0]);

    if(strcmp(s[0], "")) {
        // Metadata File
        FILE *f = ::fopen(s[0], "r");
        if(f == NULL) {
            spdlog::error("fopen of file failed with code");
            spdlog::error( std::strerror(errno));
            return STITCHES_IPC_RC_ERROR_SEVERE;
        }
        char *s = fgets(&pipeName[0], sizeof(pipeName), f);
        fclose(f);
        if(s == NULL) {
            return STITCHES_IPC_RC_ERROR_SEVERE;
        }
        while((strlen(pipeName) > 0) && ((pipeName[strlen(pipeName)-1] == 10) || pipeName[strlen(pipeName)-1] == 13)) {
            pipeName[strlen(pipeName) - 1] = 0;
        }
    } else {
        if(s[1] == NULL) {
            return STITCHES_IPC_RC_ERROR_SEVERE;
        }
        strncpy(&pipeName[0], s[1], sizeof(pipeName));
        pipeName[sizeof(pipeName)-1] = 0;
    } 

    return STITCHES_IPC_RC_OK;
}
 
int StitchesIPCPosixNamedPipe::readBytes(int fd, void *buf, int size) {
    int count = 0;
    int rc;
    while(count != size) {
        rc = ::read(fd, &((unsigned char *)buf)[count], size - count);
        if(rc == 0)  return STITCHES_IPC_RC_TERM;
        if(rc == -1) return STITCHES_IPC_RC_ERROR_SEVERE;
        count += rc;
    }
    return STITCHES_IPC_RC_OK;
}

int StitchesIPCPosixNamedPipe::writeBytes(int fd, void *buf, int size) {
    int rc = ::write(fd, buf, size);
    if(rc == -1) {
       if(errno == EPIPE) return STITCHES_IPC_RC_TERM;
       return STITCHES_IPC_RC_ERROR_SEVERE;
    }
    return STITCHES_IPC_RC_OK;
}
}

