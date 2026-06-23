import bpy
from ..core import memory

class MIDIDRONECONTROL_OT_trigger_pad(bpy.types.Operator):
    bl_idname = "mdc.trigger_pad"
    bl_label = "Trigger Pad"
    
    pad_index: bpy.props.IntProperty()

    def execute(self, context):
        sc = context.scene
        current_frame = sc.frame_current
        
        # Retrieve from high speed dictionary cache
        payload = memory.active_payloads.get(self.pad_index)
        if not payload:
            return {'FINISHED'}
            
        target_layer = sc.mdc_target_layer if sc.mdc_layer_mode == 'MULTI' else "md_layer_1"
        
        for drone_name, channels in payload.items():
            # Drone Level Cooldown (Option B Gatekeeper)
            if drone_name in memory.drone_cooldowns:
                if current_frame < memory.drone_cooldowns[drone_name]:
                    continue # Skip this drone, it's busy executing a prior command
            
            obj = bpy.data.objects.get(drone_name)
            if not obj:
                continue
                
            if not obj.animation_data:
                obj.animation_data_create()
            if not obj.animation_data.action:
                obj.animation_data.action = bpy.data.actions.new(name=f"{drone_name}_Action")
                
            action = obj.animation_data.action
            max_pad_frame_offset = 0
            
            # Write data channels
            for array_idx_str, keys in channels.items():
                array_idx = int(array_idx_str)
                data_path = f'["{target_layer}"]'
                
                # Look for existing F-curve or create one
                fcurve = action.fcurves.find(data_path, index=array_idx)
                if not fcurve:
                    fcurve = action.fcurves.new(data_path, index=array_idx)
                
                for offset_frame, value in keys:
                    target_f = current_frame + offset_frame
                    fcurve.keyframe_points.insert(target_f, value, options={'FAST'})
                    if offset_frame > max_pad_frame_offset:
                        max_pad_frame_offset = offset_frame
                        
                fcurve.update()
                
            # Lock drone until this complete sample chunk has finished executing
            memory.drone_cooldowns[drone_name] = current_frame + max_pad_frame_offset
            
        # Force redraw of the screen to give real-time viewport changes
        context.area.tag_redraw()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MIDIDRONECONTROL_OT_trigger_pad)

def unregister():
    bpy.utils.unregister_class(MIDIDRONECONTROL_OT_trigger_pad)