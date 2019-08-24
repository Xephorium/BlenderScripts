import bpy
from random import randrange

# File:             RandomizeKeyframedLocationOffset.py
# Date:             08.21.2019
# Version:          Blender 2.8
#
# This script randomizes the offset of keyframed location curves for selected objects.
#
# Instructions:
#   1. Select All Keyframed Objects
#   3. Run Script


MIN_OFFSET = 0
MAX_OFFSET = 40


# Main Program
def main():
   
    # Get Object List
    object_list = bpy.context.selected_objects
   
    # For Each Object
    for object in object_list:
        object_curves = object.animation_data.action.fcurves
        
        # Determine Offset
        offset = randrange(MIN_OFFSET, MAX_OFFSET)
        print(offset)
        
        # For Each Location Keyframe
        for curve in object_curves:
            if curve.data_path == "location": # or curve.data_path == "box":
                for keyframe_point in curve.keyframe_points:
                    
                    # Advance By Offset
                    keyframe_point.co.x = keyframe_point.co.x + offset

if __name__ == '__main__':
    main()