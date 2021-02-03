/*
 * Copyright Systems & Technology Research 2020
 * Usage of this software is governed by the LICENSE file accompanying the distribution. 
 * By downloading, copying, installing or using the software you agree to this license.
 */

package com.str.sosite.generator.cpp

import com.str.sosite.HCALRuntimeConfiguration
import com.str.sosite.generator.cpp.utilities.LoggersCpp
import com.str.sosite.representations.periphery.stack.PeriphFieldStackRef
import com.str.sosite.representations.periphery.stack.PeriphSSIMidCallbackStackLayer
import com.str.sosite.representations.periphery.stack.PeriphSSInterface
import com.str.sosite.representations.periphery.stack.PeriphUnitTestTargetStackLayer
import java.util.ArrayList
import java.util.Collections
import java.util.List

import static com.str.sosite.generator.utilities.StringFunctions.*

import static extension com.str.sosite.representations.periphery.LayerInputs.*
import static extension com.str.sosite.representations.periphery.StringRepresentations.*

class CppClassGenerator {

  def String compileLayers(CppLayerGenerator layerGen) {
    
    // combined extra class members
    var extraMembers = new ArrayList<String>
    extraMembers.addAll(layerGen.compileExtraMembers)

    var inheritance = new ArrayList<String>
    inheritance.addAll(layerGen.compileInheritance)

    // combined extra class methods
    var extraMethods = new ArrayList<String>
    extraMethods.addAll(layerGen.compileExtraMethods())
      
    // input types to iterate over
    var List<PeriphFieldStackRef> inTypes = new ArrayList()
    inTypes.addAll( layerGen.layer.mInputTypes )

    // handle special cases for serialized input
    if (layerGen.layer.isSinglePipeSerializedInput) { // special case for untagged serialized data - use single process method
      // only want to create one process() method, so modify inTypes
      //FIXME: this is really wrong; the layer should onlu have a single input type indicating serialize data of some kind
      // can we not just come up with a tagging interface that indicates a serialized message
      val message = new PeriphFieldStackRef(null,inTypes.get(0).mRef);
      inTypes = Collections.singletonList(message);
    } else if (inTypes.length > 1 && layerGen.layer.isInputSerialized) { // serialized input, so only create one process method per source type
      var foundTypes = new ArrayList<String>
      var newList = new ArrayList<PeriphFieldStackRef>
      for (input : inTypes) {
        val virtualSourceName = if (input.mVirtualSource !== null) input.mVirtualSource.mName else '<NULL>'
        if (!foundTypes.contains(virtualSourceName)) {
          foundTypes.add(virtualSourceName)
          newList.add(input)
        }
      }
      inTypes = newList
    }

    // is this a terminal SSI layer?
    val callbackClass =
      if ( layerGen.layer instanceof PeriphSSIMidCallbackStackLayer ) {
        val ssi = layerGen.layer.findParent(PeriphSSInterface)
        val ssi_decl = ssi.parent
        '''«ssi_decl.mName.replace(".","::")»::SSI::«ssi.mInterfaceName»::«ssi.mInterfaceName»CallbackInterface'''
      } else null
    
    // assemble code
    
    val header_guard = layerGen.qualifiedLayerName.toString("_") + "_H"

    var includes = layerGen.compileIncludes()
    includes.add('<iostream>')
    layerGen.isSynchronizedProcess() {
    }
    
    return '''
    «getRenderedHeaderString»
       
    #ifndef «header_guard»
    #define «header_guard»
 
    #include "mil/darpa/sosite/stitches/stitcheslib"
    #include "spdlog/spdlog.h"
    
    «FOR i : includes.toSet()»#include «i»
    «ENDFOR»

    «FOR ns : layerGen.getLayer().mId.mPackageName.segments»
    namespace «ns» {
  	«ENDFOR»
    
    /**
     * @generated
     *
     */
    
    class «layerGen.classname» {

    «layerGen.compileFriendClasses»

    	public:
        
        // constructor
        «IF callbackClass !== null»
          «layerGen.classname»( «callbackClass»* ipCallback) {
            «layerGen.compileConstructor»
            mbIsInitialized = false; // layer has not been initialized yet
            mpCallback = ipCallback;
            spdlog::info("Received callback {} assigned {}", (void*)ipCallback, (void*)mpCallback);
          }
        «ELSE»
          «layerGen.classname»( «layerGen.nextLayersAll.map[x|x.mId.mFQName.toString("::") + '* ipNextLayer' + layerGen.nextLayersAll.indexOf(x)].join(', ')» ) {
            «layerGen.compileConstructor»
            mbIsInitialized = false; // layer has not been initialized yet
            «FOR layer : layerGen.nextLayersAll»
              mpNextLayer«layerGen.nextLayersAll.indexOf(layer)» = ipNextLayer«layerGen.nextLayersAll.indexOf(layer)»;
            «ENDFOR»
          }
        «ENDIF»
      
        // initialization
        bool init() {
        	if ( mbIsInitialized == false )
        	{
            spdlog::info("Starting layer init: «layerGen.qualifiedLayerName.toString("::")»");
            bool result = true; // start assuming success
            // START INITIALIZATION OF DOWNSTREAM LAYERS IN OTHER CLASSES
            «FOR layer : layerGen.nextLayersAll»
              result = mpNextLayer«layerGen.nextLayersAll.indexOf(layer)»->init() && result;
            «ENDFOR»
            // END INITIALIZATION OF DOWNSTREAM LAYERS IN OTHER CLASSES
            «layerGen.compileInit»
            mbIsInitialized = true;
            spdlog::info("Completed layer init: «layerGen.qualifiedLayerName.toString("::")»");
            return result;
          }
          else
          {
          	// don't initialize twice (e.g. splitter into combiner)
          	spdlog::info("Layer init already complete, will not init twice: «layerGen.qualifiedLayerName.toString("::")»");
          	return true;
          }
        }
    
        // return true if this layer and any subsequent layers are initialized
        bool isInitialized() {
          «IF layerGen.nextLayersAll.length > 0»
            return «layerGen.compileIsInitialized('mbIsInitialized')» && «layerGen.nextLayersAll.map[x|'mpNextLayer' + layerGen.nextLayersAll.indexOf(x) + '->isInitialized()'].join(' && ')»;
          «ELSE»
            return «layerGen.compileIsInitialized('mbIsInitialized')»;
          «ENDIF»
        }

        // de-initialize layer
        bool deinit() {
        	if ( mbIsInitialized == true )
        	{
        		spdlog::info("Starting layer deinit: «layerGen.qualifiedLayerName.toString("::")»");
            bool result = true; // start assuming success
            // START DE-INITIALIZATION OF DOWNSTREAM LAYERS IN OTHER CLASSES
            «FOR layer : layerGen.nextLayersAll»
              result = mpNextLayer«layerGen.nextLayersAll.indexOf(layer)»->deinit() && result;
            «ENDFOR»
            // END DE-INITIALIZATION OF DOWNSTREAM LAYERS IN OTHER CLASSES
            «layerGen.compileDeinit»
            mbIsInitialized = false;
            spdlog::info("Completed layer deinit: «layerGen.qualifiedLayerName.toString("::")»");
            return result;
          }
          else
          {
          	// don't deinitialize twice (e.g. splitter into combiner)
          	spdlog::info("Layer deinit already complete, will not deinit twice: «layerGen.qualifiedLayerName.toString("::")»");
          	return true;
          }
        }
      
        /*
         * Message processing methods below
         */

        «FOR input_type : inTypes»
          // process message: «input_type.stringRep»
          bool process«input_type.processMessageName( !layerGen.layer.isSinglePipeSerializedInput )»(«layerGen.cppInputType(input_type)» «layerGen.getVar('ipMessage')») {
            «IF layerGen.isSynchronizedProcess»mil::darpa::sosite::stitches::Lock<mil::darpa::sosite::stitches::Mutex> lockguard(mProcessFnLock);«ENDIF»
            bool result = true;
            // START MESSSAGE PROCESSING
            spdlog::info("Start of message processing");

              try {
                «compileProcess(layerGen, input_type, layerGen.getVar('ipMessage'))»
              } catch( std::exception& e) {
              	result = false;
                spdlog::error("ERROR: caught exception in «layerGen.qualifiedLayerName» {}", e.what());
                «IF layerGen.layer instanceof PeriphUnitTestTargetStackLayer»
                spdlog::error("ERROR: caught exception in UnitTestTarget layer, will exit with error code (unit test should fail)");
                exit(255);
                «ENDIF»
                return result;
              } catch( ... ) {
              	result = false;
                spdlog::error("ERROR: caught exception in «layerGen.qualifiedLayerName»");
                «IF layerGen.layer instanceof PeriphUnitTestTargetStackLayer»
                spdlog::error("ERROR: caught exception in UnitTestTarget layer, will exit with error code (unit test should fail)");
                exit(255);
                «ENDIF»
                return result;
              }
            spdlog::info("End of message processing");
            // END MESSAGE PROCESSING
            «IF layerGen.isImplicitReturn»return result;«ENDIF»
          }

        «ENDFOR»
      
        /*
         * Extra methods below
         */
       
        «extraMethods.join('\n\n')»
      
    	private:
      
        // class properties
        bool mbIsInitialized;
        mil::darpa::sosite::stitches::Mutex mProcessFnLock;
        «FOR layer : layerGen.nextLayersAll»
          «layer.mId.mFQName.toString("::")»* mpNextLayer«layerGen.nextLayersAll.indexOf(layer)»;
        «ENDFOR»
        «extraMembers.join('\n')»
    };
    
    «layerGen.compileStaticClassMemberInitializers().join('\n')»
    
    «FOR ns : layerGen.getLayer().mId.mPackageName.segments»
    }
  	«ENDFOR»
    
    #endif
  '''
  }

  def private String compileProcess(CppLayerGenerator layerGen, PeriphFieldStackRef input_type, String inVar) {
    return '''
      // START PROCESSING FOR «layerGen.qualifiedLayerName.toString("::")»: «inVar» -> «layerGen.getVar('inner')»
        «IF HCALRuntimeConfiguration.generateLogging»«LoggersCpp.preLog(layerGen.layer)»«ENDIF»
        «IF HCALRuntimeConfiguration.generateNoTimingLayerLogs»«LoggersCpp.preLogNoTime(layerGen.layer, layerGen.cppInputType( input_type ) )»«ENDIF»
        «layerGen.compileProcess(input_type, inVar, layerGen.getVar('inner'))»
      // END PROCESSING FOR «layerGen.qualifiedLayerName.toString("::")»
    '''
  }
}
