/*
 * Copyright Systems & Technology Research 2020
 * Usage of this software is governed by the LICENSE file accompanying the distribution. 
 * By downloading, copying, installing or using the software you agree to this license.
 */

package com.str.sosite.generator.cpp.layer

import com.galois.sosite.codegen.cpp.CppVersion
import com.str.sosite.generator.cpp.CppLayerGenerator
import com.str.sosite.representations.periphery.stack.PeriphFieldStackRef
import com.str.sosite.representations.periphery.stack.PeriphSSIMidCallbackStackLayer
import com.str.sosite.representations.periphery.stack.PeriphSSInterface
import com.str.sosite.ssilintgenerator.HCALILSSILINTGeneratorUpperMid
import java.util.ArrayList
import java.util.List

import static com.str.sosite.generator.cpp.HCALILCppTypes.*
import static com.str.sosite.representations.periphery.StringRepresentations.*

import static extension com.str.sosite.representations.periphery.LayerInputs.*

class CppSSIMidCallbackGenerator extends CppLayerGenerator {
  
  // constructors
  new(CppVersion ver,PeriphSSIMidCallbackStackLayer iLayer) {
    super(ver,iLayer)
  }
  
  // imports/includes required
  override def List<String> compileIncludes() {
    var includes = super.compileIncludes()
    val ssi = layer.findParent(PeriphSSInterface);
    val ssi_decl = ssi.mParentInterface
    if (ssi_decl !== null && HCALILSSILINTGeneratorUpperMid.isReceiver(ssi.mStack)) {
      val callback_class = '''«ssi_decl.mName».SSI.«ssi.mInterfaceName».«ssi.mInterfaceName»CallbackInterface'''
      includes.add('<' + callback_class.toString.replace('.', '/') + '.hpp>')
    }
    return includes
  }
  
  // add extra class members
  override def compileExtraMembers() {
    val extra_members = new ArrayList<String>
    val ssi = layer.findParent(PeriphSSInterface);
    val ssi_decl = ssi.mParentInterface
    val callback_class = '''«ssi_decl.mName.replace(".","::")»::SSI::«ssi.mInterfaceName»::«ssi.mInterfaceName»CallbackInterface'''
    extra_members.add( '''«callback_class»* mpCallback;''' )
    return extra_members
  }

  // override process method
  override compileProcess(PeriphFieldStackRef inputType, String inVar, String outVar) {
    return '''
      try {
        // NOTE: this is a copy for now because of Required vs. StitchesPtr, and SSIMid callback API must remain the same
        mil::darpa::sosite::stitches::StitchesPtr< «toCppType( inputType.mRef )» > msgPtr = mil::darpa::sosite::stitches::make_shared< «toCppType( inputType.mRef )» >( *«inVar» );
        result &= mpCallback->process«inputType.processMessageName(true)»( msgPtr );
      } catch( std::exception& e ) {
        spdlog::error("ERROR: callback to SSIUpper extension (user written code to get STITCHES msg into core data structure and on to the SS core)) threw an exception! («layer.mId.mFQName» «stringRep(inputType)») : {}", e.what());
        return false;
      } catch( ... ) {
        spdlog::error("ERROR: callback to SSIUpper extension (user written code to get STITCHES msg into core data structure and on to the SS core)) threw an exception! («layer.mId.mFQName» «stringRep(inputType)»)");
        return false;
      }
    '''
  }
}
