import bpy
import json

class MIDIDRONECONTROL_OT_patch_shader(bpy.types.Operator):
    bl_idname = "mdc.patch_shader"
    bl_label = "Patch ALC Shader for Live Preview"
    
    def execute(self, context):
        sc = context.scene
        if not context.active_object or not context.active_object.active_material:
            self.report({'WARNING'}, "Please select a drone with active material first!")
            return {'CANCELLED'}

        # 1. SCAN PADS TO FIND WHICH LAYERS ARE ACTUALLY SAMPLED
        used_layers = set()
        if sc.mdc_banks:
            for bank in sc.mdc_banks:
                for pad in bank.pads:
                    if pad.json_payload and pad.json_payload != "{}":
                        try:
                            payload = json.loads(pad.json_payload)
                            used_layers.add(payload.get("layer", "Layer_1"))
                        except Exception: pass
                        
        if not used_layers:
            self.report({'WARNING'}, "No samples found! Sample a pad first so the patcher knows what to build.")
            return {'CANCELLED'}
            
        mat = context.active_object.active_material
        tree = mat.node_tree
        if not tree: return {'CANCELLED'}
            
        driver_node = tree.nodes.get("MDC_State_Driver")
        if not driver_node:
            driver_node = tree.nodes.new(type="ShaderNodeValue")
            driver_node.name = "MDC_State_Driver"
            driver_node.label = "MDC Master Switch"
            driver_node.location = (-1000, 400) 
            driver_node.outputs[0].default_value = 0.0

        # 2. FIND ONLY THE ATTRIBUTES FOR THOSE SAMPLED LAYERS
        layer_attributes = []
        for node in tree.nodes:
            if node.type == 'ATTRIBUTE' and node.attribute_name.startswith("Layer_"):
                if not node.attribute_name.endswith("_live"):
                    if node.attribute_name in used_layers:
                        layer_attributes.append(node)
                    
        patched_count = 0
        for attr_node in layer_attributes:
            ghost_name = f"{attr_node.attribute_name}_live"
            if tree.nodes.get(f"Ghost_{attr_node.attribute_name}"): continue
                
            frame = tree.nodes.new(type='NodeFrame')
            frame.name = f"Frame_{attr_node.attribute_name}"
            frame.label = f"MDC Live Override ({attr_node.attribute_name})"
                
            ghost_node = tree.nodes.new(type='ShaderNodeAttribute')
            ghost_node.name = f"Ghost_{attr_node.attribute_name}"
            ghost_node.attribute_name = ghost_name
            ghost_node.attribute_type = 'OBJECT'
            ghost_node.location = (attr_node.location.x, attr_node.location.y - 300) 
            ghost_node.parent = frame

            math_node = tree.nodes.new(type='ShaderNodeMath')
            math_node.name = f"Math_{attr_node.attribute_name}"
            math_node.operation = 'MULTIPLY'
            math_node.location = (attr_node.location.x + 300, attr_node.location.y - 150)
            math_node.parent = frame

            mix_node = tree.nodes.new(type='ShaderNodeMix')
            mix_node.data_type = 'RGBA'
            mix_node.blend_type = 'MIX'
            mix_node.location = (attr_node.location.x + 600, attr_node.location.y)
            mix_node.parent = frame
            
            # The Alpha Hack Wiring
            tree.links.new(driver_node.outputs[0], math_node.inputs[0])
            tree.links.new(ghost_node.outputs['Alpha'], math_node.inputs[1]) 
            tree.links.new(math_node.outputs['Value'], mix_node.inputs['Factor'])
            
            for link in list(attr_node.outputs['Color'].links):
                tree.links.new(mix_node.outputs['Result'], link.to_socket)
                
            tree.links.new(attr_node.outputs['Color'], mix_node.inputs['A'])
            tree.links.new(ghost_node.outputs['Color'], mix_node.inputs['B'])
            patched_count += 1
            
        self.report({'INFO'}, f"Successfully patched {patched_count} active layers for Live Preview!")
        return {'FINISHED'}

def register(): bpy.utils.register_class(MIDIDRONECONTROL_OT_patch_shader)
def unregister(): bpy.utils.unregister_class(MIDIDRONECONTROL_OT_patch_shader)