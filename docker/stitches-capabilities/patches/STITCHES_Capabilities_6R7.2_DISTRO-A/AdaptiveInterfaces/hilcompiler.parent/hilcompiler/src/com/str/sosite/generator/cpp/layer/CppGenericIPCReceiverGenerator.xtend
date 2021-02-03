/*
 * Copyright Systems & Technology Research 2020
 * Usage of this software is governed by the LICENSE file accompanying the distribution. 
 * By downloading, copying, installing or using the software you agree to this license.
 */

package com.str.sosite.generator.cpp.layer

import com.galois.sosite.codegen.cpp.CppVersion
import com.str.sosite.HCALRuntimeConfiguration
import com.str.sosite.generator.cpp.CppLayerGenerator
import com.str.sosite.generator.cpp.utilities.LoggersCpp
import com.str.sosite.representations.periphery.stack.PeriphCppIPCLibraryDetails
import com.str.sosite.representations.periphery.stack.PeriphFieldStackRef
import com.str.sosite.representations.periphery.stack.PeriphGenericIPCReceiverStackLayer
import java.util.ArrayList
import java.util.List

class CppGenericIPCReceiverGenerator extends CppLayerGenerator {
  
  // constructors
  new(CppVersion ver,PeriphGenericIPCReceiverStackLayer iLayer) {
    super(ver,iLayer)
  }
  
	override PeriphGenericIPCReceiverStackLayer getLayer() {
		super.layer as PeriphGenericIPCReceiverStackLayer;
	}

  def libraryDetails() {
    layer.mIPCLibraryDetails.filter[x|x instanceof PeriphCppIPCLibraryDetails].head as PeriphCppIPCLibraryDetails
  }
  
  def libraryInstanceClassName() {
    libraryDetails.fqClassName
  }
  
  private def String logfile()
  {
  	if (HCALRuntimeConfiguration.recordIPCMessages>0) {
  		return layer.mId.mFQName.toString("_")+"_message.log";
  	}
  	else {
  		return null;
  	}
  }
  
  // return the java equivalent for a layer input type
  override def cppInputType(PeriphFieldStackRef ref) {
    return 'const std::string&'
  }
  
  // imports/includes required
  override def List<String> compileIncludes() {
    var includes = super.compileIncludes()
    includes.add( "<" + libraryDetails.includeHeader + ">" )
    includes.add( "<iostream>" )
    if (logfile!==null) {
	    includes.add( "<fstream>" )
    }
    return includes
  }
  
  // add extra methods
  override def compileExtraMethods() {
    val out = new ArrayList<String>
    out.add(libraryOpener)
    out.add(requestBuf)
    out.add(runMethod())
    return out
  }
  
  // add extra class members
  override def compileExtraMembers() {
    val extra_members = new ArrayList<String>
    if (logfile!==null) {
    	extra_members.add( '''size_t  «getVar("mNumRecorded")»;''' );
    	extra_members.add( '''std::ofstream «getVar("mMessageFile")»;''' );
    }
    
    extra_members.add( '''bool «getVar('mbKeepRunning')»;''' )
    extra_members.add( '''mil::darpa::sosite::stitches::Thread «getVar('mIPCLibraryOpenerThread')»;''' )
    extra_members.add( '''volatile bool «getVar('mbIPCLibraryOpen')»;''' )
    extra_members.add( '''mil::darpa::sosite::stitches::Mutex «getVar('mMutex')»;''' )
    extra_members.add( libraryInstanceClassName() + ''' «getVar('mIPCLibraryInstance')»;''' )
    return extra_members
  }
  
  override def compileStaticClassMemberInitializers() {
    val initializers = new ArrayList<String>
    return initializers
  }
  
  // definition of constructor
  override def compileConstructor() {
    return '''
      «IF logfile!==null»
      «getVar("mNumRecorded")» = 0;
      «getVar("mMessageFile")».open("«logfile»",::std::ios_base::binary|::std::ios_base::out);
      «ENDIF»
      «getVar('mbKeepRunning')» = true;
      «getVar('mbIPCLibraryOpen')» = false;
      '''
  }

  def configParamsJoined() {
    libraryDetails.configurationStringList.join('",\n"')
  }

  def configParamsJoinedComma() {
    libraryDetails.configurationStringList.join('\',\'')
  }
  
  // override init method
  override compileInit() {
    '''
      static const char *config_params[ «libraryDetails.configurationStringList.length + 1» ] =
      {
        "«configParamsJoined()»",
        (char *)0
      };
      int «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».initReceive( config_params, &«qualifiedLayerName.toString("::")»::requestBufCallback );
      if ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) {
        std::cerr << "ERROR returned by «libraryInstanceClassName»::initReceive(...): " << «getVar('ret_code')» << ", " << «getVar('mIPCLibraryInstance')».getLastError() << " (" << "'«configParamsJoinedComma()»'" << ")" << std::endl;
        return false;
      }
      «getVar('mIPCLibraryOpenerThread')» = mil::darpa::sosite::stitches::Thread( &«qualifiedLayerName.toString("::")»::startIPCLibraryOpenThread, this );
    '''
  }
  
  // override deinit method
  override compileDeinit() {
    '''
      «getVar('mbKeepRunning')» = false;
      «getVar('mIPCLibraryOpenerThread')».join();
      int «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».term();
      mil::darpa::sosite::stitches::Lock<mil::darpa::sosite::stitches::Mutex> lockguard(«getVar('mMutex')»);
      if ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) {
        spdlog::error("ERROR returned by «libraryInstanceClassName»::term(): {},{} ({})", «getVar('ret_code')», «getVar('mIPCLibraryInstance')».getLastError(), "'«configParamsJoinedComma()»'");
        return false;
      }
    '''
  }
  
  override compileIsInitialized(String initVar) {
    return '''«initVar» && «getVar('mbIPCLibraryOpen')»'''
  }
  
  // override process method
  override compileProcess(PeriphFieldStackRef inputType, String inVar, String outVar) {
  
  	val logger = 
  		'''	
  		«IF logfile!==null»
  			if (mMessageFile.is_open()) {
  				mMessageFile.put((char)((«inVar».length() >> 24)&0xff));
  				mMessageFile.put((char)((«inVar».length() >> 16)&0xff));
  				mMessageFile.put((char)((«inVar».length() >> 8)&0xff));
  				mMessageFile.put((char)((«inVar».length() >> 0)&0xff));
  				mMessageFile.write(«inVar».c_str(), «inVar».length());
  				mMessageFile << ::std::flush;
  				if (++«getVar('mNumRecorded')» >= «HCALRuntimeConfiguration.recordIPCMessages») {
  					std::cerr << "INFO: recorded «HCALRuntimeConfiguration.recordIPCMessages» requested messages" << ::std::endl;
  					mMessageFile.close(); 
  				}
  			}

          «ENDIF»
		''';
		    
    if ( layer.mSerializationIds.empty ) {
      return logger + noOp(inputType, inVar, outVar, true)
    } else {
      val checkData = layer.mSerializationIds
        .map[i|'''(unsigned char)«inVar»[0]==(unsigned char)«i»''']
        .join(' || ')
      return '''
        if («checkData») {
          «IF HCALRuntimeConfiguration.generateNoTimingLayerLogs»std::cout << "«layer.mId.mFQName» Generic IPC Receiver forwarding packet with ID " << «inVar»[0] << std::endl;«ENDIF»
          «logger»
          «noOp(inputType, inVar, outVar, true)»
        } else {
          «IF HCALRuntimeConfiguration.generateNoTimingLayerLogs»std::cout << "«layer.mId.mFQName» Generic IPC Receiver dropping packet with ID " << «inVar»[0] << std::endl;«ENDIF»
        }
      '''
    }
  }
  
  // IPC library opener
  def String libraryOpener() {
    '''
      void startIPCLibraryOpenThread()
      {
        spdlog::info("«layer.mId.mFQName.toString("::")»: attempting to «libraryInstanceClassName»::open()");
        int «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».open();
        size_t «getVar('attempt_counter')» = 0;
        size_t «getVar('retry_sleep_ms')» = 10;
        while ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) {
          if ( «getVar('ret_code')» == STITCHES_IPC_RC_RETRY ) {
            // sleep a little and retry open()
            mil::darpa::sosite::stitches::sleep_for_millis( «getVar('retry_sleep_ms')» );
            «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».open();
            «getVar('attempt_counter')»++;
          } else {
            std::cerr << "ERROR returned by «libraryInstanceClassName»::open(): " << «getVar('ret_code')» << ", " << «getVar('mIPCLibraryInstance')».getLastError() << " ; stopping attempts to open library" << " (" << "'«configParamsJoinedComma()»'" << ")" << std::endl;
            break;
          }
          if ( «getVar('attempt_counter')» % 500 == 0 ||  «getVar('retry_sleep_ms')» >= 1000) {
            spdlog::info("«layer.mId.mFQName.toString("::")»: still attempting to «libraryInstanceClassName»::open(), most recently got back {}", «getVar('ret_code')»);
            if ( «getVar('retry_sleep_ms')» == 10 ) {
              «getVar('retry_sleep_ms')» = 100;
            } else if ( «getVar('retry_sleep_ms')» == 100 ) {
              «getVar('retry_sleep_ms')» = 1000;
            } else if ( «getVar('retry_sleep_ms')» == 1000 ) {
              «getVar('retry_sleep_ms')» = 5000;
            }
          }
        }

        if ( «getVar('ret_code')» == STITCHES_IPC_RC_OK ) {
          spdlog::info("«layer.mId.mFQName.toString("::")»: succeeded with «libraryInstanceClassName»::open()");
          «getVar('mbIPCLibraryOpen')» = true;
        }
      }'''
  }
  
  def String requestBuf() {
    '''
      static unsigned char* requestBufCallback( size_t size ) {
        return (unsigned char*)malloc( size );
      }
    '''
  }
  
  // threaded run method
  def String runMethod() {
    return '''
      void run() {
        «getVar('mIPCLibraryOpenerThread')».join();
        // acquiring lock so that "run" method will wait for init to complete before running and
        //  prevent deinit from closing library until run returns
        mil::darpa::sosite::stitches::Lock<mil::darpa::sosite::stitches::Mutex> lockguard(«getVar('mMutex')»);
        if ( «getVar('mbIPCLibraryOpen')» ) {
          // message receive loop
          unsigned char* «getVar('p_buf_from_read')» = NULL;
          size_t «getVar('num_bytes_read')» = 0;
          int «getVar('ret_code')» = STITCHES_IPC_RC_OK;
          size_t «getVar('read_fail_counter')» = 0;
          size_t «getVar('read_fail_sleep_ms')» = 10;
          while ( «getVar('mbKeepRunning')» ) {
            «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».read( &«getVar('p_buf_from_read')», &«getVar('num_bytes_read')» );
            if ( ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) && ( «getVar('mbKeepRunning')» == true ) ) {
              if ( «getVar('read_fail_counter')» % 500 == 0 ||  «getVar('read_fail_sleep_ms')» >= 1000) {
                std::cerr << "ERROR returned by «libraryInstanceClassName»::read(): " << «getVar('ret_code')» << ", " << «getVar('mIPCLibraryInstance')».getLastError() << " (" << "'«configParamsJoinedComma()»'" << ")" << " after " << «getVar('read_fail_counter')» << " tries" << std::endl;
                if ( «getVar('read_fail_sleep_ms')» == 10 ) {
                  «getVar('read_fail_sleep_ms')» = 100;
                } else if ( «getVar('read_fail_sleep_ms')» == 100 ) {
                  «getVar('read_fail_sleep_ms')» = 1000;
                } else if ( «getVar('read_fail_sleep_ms')» == 1000 ) {
                  «getVar('read_fail_sleep_ms')» = 5000;
                }
              }
              «getVar('read_fail_counter')»++;
              // sleep a little before retry read()
              mil::darpa::sosite::stitches::sleep_for_millis( «getVar('read_fail_sleep_ms')» );
            } else if ( «getVar('mbKeepRunning')» ) {
              «getVar('read_fail_counter')» = 0;
              // allocate a string of the proper size to hold the message
              std::string «getVar('message')»;
              «getVar('message')».resize( «getVar('num_bytes_read')» );
              
              
              // write the received data into the final buffer at the correct position
              memcpy((void*)(«getVar('message')».data()), (void*)«getVar('p_buf_from_read')», «getVar('num_bytes_read')»);
              free( «getVar('p_buf_from_read')» );

              
              «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.preLog(layer)»«ENDIF»
              «IF HCALRuntimeConfiguration.generateNoTimingLayerLogs»std::cout << "«layer.mId.mFQName.toString( "::")»: Read from '«libraryInstanceClassName»': message size = " << «getVar('num_bytes_read')» << std::endl;«ENDIF»
              «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.postLog(layer)»«ENDIF»
              process(«getVar('message')»);
              «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.returnLog(layer)»«ENDIF»
            }
          }
        } else {
        	«IF layer.insideSSI»
        	std::cerr << "WARNING: «libraryInstanceClassName»::open() failed and is most likely caused by a disabled interface" << std::endl;
        	«ELSE»
        	std::cerr << "ERROR: «libraryInstanceClassName»::open() failed, will NOT proceed with main while loop to read from IPC library!" << std::endl;
        	«ENDIF»
        }
        int «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».close();
        if ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) {
          std::cerr << "ERROR returned by «libraryInstanceClassName»::close(): " << «getVar('ret_code')» << ", " << «getVar('mIPCLibraryInstance')».getLastError() << " (" << "'«configParamsJoinedComma()»'" << ")" << std::endl;
        }
      }
    '''
  }

}
