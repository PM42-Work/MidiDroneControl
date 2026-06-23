bl_info = {
    "name": "Midi Drone Control",
    "author": "Raghuvansh Agarwal",
    "version": (1, 0, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Midi Drone Control",
    "description": "MIDI-triggered sample pad for live drone light busking",
    "category": "3D View",
}

import bpy
import sys, os, platform

# Add dependencies path so Blender can find our MIDI libraries
current_dir = os.path.dirname(os.path.realpath(__file__))
system_platform = platform.system().lower() 
dep_folder = "win" if system_platform == 'windows' else "mac" if system_platform == 'darwin' else "linux"
dep_path = os.path.join(current_dir, "dependencies", dep_folder)
if dep_path not in sys.path: 
    sys.path.insert(0, dep_path)

def register():
    pass # We will register classes here later

def unregister():
    pass # We will unregister classes here later