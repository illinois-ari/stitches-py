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
import com.str.sosite.representations.periphery.stack.PeriphGenericIPCSenderStackLayer
import java.util.ArrayList
import java.util.List

class CppGenericIPCSenderGenerator extends CppLayerGenerator {
  
  // constructors
  new(CppVersion ver,PeriphGenericIPCSenderStackLayer iLayer) {
    super(ver,iLayer)
    mbImplicitReturn = false
  }
  
  def libraryDetails() {
    (layer as PeriphGenericIPCSenderStackLayer).mIPCLibraryDetails.filter[x|x instanceof PeriphCppIPCLibraryDetails].head as PeriphCppIPCLibraryDetails
  }
  
  def libraryInstanceClassName() {
    libraryDetails.fqClassName
  }
  
  // imports/includes required
  override def List<String> compileIncludes() {
    var includes = super.compileIncludes()
    includes.add( "<" + libraryDetails.includeHeader + ">" )
    includes.add( "<iostream>" )
    return includes
  }
  
  // add extra methods
  override def compileExtraMethods() {
    val out = new ArrayList<String>
    out.add(libraryOpener)
    out.add(returnBuf)
    return out
  }
  
  // add extra class members
  override def compileExtraMembers() {
    val extra_members = new ArrayList<String>
    extra_members.add( '''bool «getVar('mbKeepRunning')»;''' )
    extra_members.add( '''mil::darpa::sosite::stitches::Thread «getVar('mIPCLibraryOpenerThread')»;''' )
    extra_members.add( '''volatile bool «getVar('mbIPCLibraryOpen')»;''' )
    extra_members.add( '''mil::darpa::sosite::stitches::Mutex «getVar('mMutex')»;''' )
    extra_members.add( libraryInstanceClassName() + ''' «getVar('mIPCLibraryInstance')»;''' )
    extra_members.add( '''int «getVar('mNumWritesFailWithTerm')»;''' )
    return extra_members
  }
  
  // definition of constructor
  override def compileConstructor() {
    return '''
      «getVar('mbKeepRunning')» = true;
      «getVar('mbIPCLibraryOpen')» = false;
      «getVar('mNumWritesFailWithTerm')» = 0;
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
      int «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».initTransmit( config_params, &«qualifiedLayerName.toString("::")»::returnBufCallback );
      if ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) {
        spdlog::error("ERROR returned by «libraryInstanceClassName»::initTransmit(...): {},{} ({})", «getVar('ret_code')», «getVar('mIPCLibraryInstance')».getLastError(), "config string '«configParamsJoinedComma()»'");
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
      mil::darpa::sosite::stitches::Lock<mil::darpa::sosite::stitches::Mutex> lockguard(«getVar('mMutex')»); // prevent library from closing until run is complete
      int «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».close();
      if ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) {
        spdlog::error("ERROR returned by «libraryInstanceClassName»::close(): {},{} ({})", «getVar('ret_code')», «getVar('mIPCLibraryInstance')».getLastError(), "config string '«configParamsJoinedComma()»'");
        return false;
      }
    '''
  }
  
  override compileIsInitialized(String initVar) {
    return '''«initVar» && «getVar('mbIPCLibraryOpen')»'''
  }
  
  // override process method
override compileProcess(PeriphFieldStackRef inputType, String inVar, String outVar) {
    return '''
      mil::darpa::sosite::stitches::Lock<mil::darpa::sosite::stitches::Mutex> lockguard(«getVar('mMutex')»); // prevent library from closing until run is complete
      «IF HCALRuntimeConfiguration.generateNoTimingLayerLogs»std::cout << "«layer.mId.mFQName.toString("::")»: Generic IPC Sender send packet with " << «inVar».length() << " bytes..." << std::endl;«ENDIF»
      
      int «getVar('ret_code')» = «getVar('mIPCLibraryInstance')».write( (unsigned char*)«inVar».c_str(), «inVar».length() );
      if ( «getVar('ret_code')» != STITCHES_IPC_RC_OK ) {
        returnBufCallback( (unsigned char*)«inVar».c_str() );
        if ( «getVar('ret_code')» == STITCHES_IPC_RC_TERM ) {
          «getVar('mNumWritesFailWithTerm')»++;
          if ( ( «getVar('mNumWritesFailWithTerm')» == 1 ) || ( «getVar('mNumWritesFailWithTerm')» % 100 == 0 ) ) {
            spdlog::error("ERROR (term) returned by «libraryInstanceClassName»::write(): {},{} ({}) got {} term exceptions so far", «getVar('ret_code')», «getVar('mIPCLibraryInstance')».getLastError(), "config string '«configParamsJoinedComma()»'", «getVar('mNumWritesFailWithTerm')»);
          }
        } else {
          spdlog::error("ERROR returned by «libraryInstanceClassName»::write(): {},{} ({})", «getVar('ret_code')», «getVar('mIPCLibraryInstance')».getLastError(), "config string '«configParamsJoinedComma()»'");
        }
        
        «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.postLog(layer)»«ENDIF»
        «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.returnLog(layer)»«ENDIF»

        return false;
      } else {
        «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.postLog(layer)»«ENDIF»
        «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.returnLog(layer)»«ENDIF»
        return true;
      }
    '''
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
            spdlog::error("ERROR returned by «libraryInstanceClassName»::open(): {},{}  ; stopping attempts to open library ({})", «getVar('ret_code')», «getVar('mIPCLibraryInstance')».getLastError(), "config string '«configParamsJoinedComma()»'");
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
  
  def String returnBuf() {
    '''
      static void returnBufCallback( unsigned char*) {
        // do nothing because the buffer will be cleaned up when the STITCHES messages is cleaned up
        return;
      }
    '''
  }

}
