import bpy

class MIDIDRONECONTROL_OT_cleanup_live(bpy.types.Operator):
    bl_idname = "mdc.cleanup_live"
    bl_label = "Cleanup MDC Properties"
    bl_description = "Removes all _live properties from drones and triggers ALC redraw"

    def execute(self, context):
        # 1. Prevent the background timer from instantly recreating them
        if context.scene.mdc_state != 'SAFE':
            self.report({'WARNING'}, "Please switch MDC to SAFE mode before cleaning up!")
            return {'CANCELLED'}

        cleaned_count = 0
        
        # 2. Strip custom properties from all objects
        for obj in bpy.data.objects:
            keys_to_delete = [k for k in obj.keys() if k.endswith("_live") or k.endswith("_live_active")]
            if keys_to_delete:
                for k in keys_to_delete:
                    del obj[k]
                cleaned_count += 1
                obj.update_tag()
                
        # 3. Trigger ALC's Redraw Nodes operator
        try:
            bpy.ops.advlighting.redraw_nodes()
        except Exception as e:
            self.report({'WARNING'}, f"Cleaned properties, but ALC Redraw failed: {e}")
                
        self.report({'INFO'}, f"Cleaned up custom properties on {cleaned_count} drones.")
        return {'FINISHED'}

def register(): bpy.utils.register_class(MIDIDRONECONTROL_OT_cleanup_live)
def unregister(): bpy.utils.unregister_class(MIDIDRONECONTROL_OT_cleanup_live)