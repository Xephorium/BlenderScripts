import bpy
import math
import mathutils
from random import randrange

# File:             GenerateAnimatedHaloRing.py
# Date:             08.26.2019
# Version:          Blender 2.8
#
# This script duplicates one slice of a Halo ring consisting of many individual
# cube objects, keyframes location and material animations for each object,
# parents the new objects to an empty, and rotates the empty into position. The
# final result is a highly configurable, spectacular show of particulate assembly
# to make Bungo proud. Run with care; this one's a computational juggernaut.
#
# --- Instructions ---
#
# Create Ring Slice
#   1. Model an emitter object named "Emitter" representing a cross-sectional
#      slice of the final ring.
#   2. Move the emitter into position at the final ring radius.
#   3. Model a particle object named "Particle" representing each piece to be
#      assembled.
#      > Geometry should include its final shape and a smaller sphere "orb".
#      > Give cube a material called "Cube Material" with two "Value" nodes
#        named "Cube Visibility" and "Cube Brightness".
#      > Give orb a material called "Orb Material" with a "Value" node named
#        "Orb Visibility".
#   4. Run sibling script "AddParticlesToEmitter.py" to generate a particle
#      at each vertex of the emitter.
#   5. Adjust slice geometry as necessary to fit within the radial area of
#      one slice.
#
# Generate Ring Assembly Animation
#   1. Create Empty at origin called "Animation Progress Marker".
#      > Keyframe empty to rotate between 0 degrees at RING_ANIMATION_START and 180
#        degrees at RING_ANIMATION_END on the z axis. Adjust assembly curve as desired.
#      > Generate equation for resulting curve from points using MyCurveFit.com.
#      > Solve equation for x using WolframAlpha.com.
#      > Plug resulting equation into get_offset_for_slice() method.
#   2. Select all particles of the source ring slice.
#   3. Adjust parameters to match final ring dimensions and animation length.
#   4. (Optional) "Window" > "Toggle System Console" to view script progress.
#   5. (Optional) Select collection in Outliner view to hold generated objects.
#   6. Run script!
#
# Were you blinded by its majesty?
#


OUTPUT_SLICE_PROGRESS = True
PARTICLE_DRIFT_BEFORE_ASSEMBLY = True

EMITTER_NAME = "Emitter"

ASSEMBLY_ANIMATION_LENGTH = 100 # Number of Frames
ASSEMBLY_RANDOM_VARIATION = 20 # Number of Frames
ASSEMBLY_TRAVEL_DISTANCE = 30 # Distance in Blender Units
ASSEMBLY_START_VARIATION = 2 # Distance in Blender Units
ASSEMBLY_FLIGHT_VARIATION = 1 # Distance in Blender Units

# Note: RING_ANIMATION_START should match the beginning of the Animation Progress
#       Marker rotation. To account for assembly, minimum value should be:
#       ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH
RING_ANIMATION_START = 120
RING_ANIMATION_LENGTH = 3970
RING_ANIMATION_END = RING_ANIMATION_START + RING_ANIMATION_LENGTH

ORB_VISIBILITY = "Orb Visibility"
CUBE_VISIBILITY = "Cube Visibility"
CUBE_BRIGHTNESS = "Cube Brightness"
ORB_MATERIAL_SLOT_NAME = "Orb Material"
ORB_VISIBILITY_VARIATION = 20 # Number of Frames
ORB_VISIBILITY_TRANSITION_LENGTH = 20 # Number of Frame
CUBE_MATERIAL_SLOT_NAME = "Cube Material"
CUBE_VISIBILITY_TRANSITION_LENGTH = 20 # Number of Frames
CUBE_BRIGHTNESS_TRANSITION_LENGTH = 30 # Number of Frames

RING_SLICES = 4096
RING_SAMPLES = 30 # Number of Slices to Generate (Max of (RING_SLICES / 2))
SLICE_ANGLE = 360 / RING_SLICES


### Low-Level, Highly Efficient API Manipulation Functions ###

# Manually Insert Location Keyframe 
# Source: https://docs.blender.org/api/blender_python_api_2_69_10/info_quickstart.html#animation
def insert_location_keyframe(object, frame, location):
    x = 0
    y = 1
    z = 2
    
    # Ensure Object Has Animation Data
    if object.animation_data is None:
        object.animation_data_create()
        
    # Ensure Animation Data Has Action
    if object.animation_data.action is None:
        object.animation_data.action = bpy.data.actions.new(name="HaloAnimationAction")
    
    # Get Location Curves
    curve_x = 0
    curve_y = 0
    curve_z = 0
    if len(object.animation_data.action.fcurves) == 0:
        curve_x = object.animation_data.action.fcurves.new(data_path="location", index=x)
        curve_y = object.animation_data.action.fcurves.new(data_path="location", index=y)
        curve_z = object.animation_data.action.fcurves.new(data_path="location", index=z)
    else:
        curve_x = object.animation_data.action.fcurves[x]
        curve_y = object.animation_data.action.fcurves[y]
        curve_z = object.animation_data.action.fcurves[z]
    
    # Add Keyframes
    curve_x.keyframe_points.add(1)
    curve_x.keyframe_points[len(curve_x.keyframe_points) - 1].co = frame, location[x]
    curve_y.keyframe_points.add(1)
    curve_y.keyframe_points[len(curve_y.keyframe_points) - 1].co = frame, location[y]
    curve_z.keyframe_points.add(1)
    curve_z.keyframe_points[len(curve_z.keyframe_points) - 1].co = frame, location[z]


### Utility Functions ###

def duplicate_particle(particle):
    
    # Create Particle Object
    new_particle = particle.copy()
    new_particle.data = particle.data.copy()
    new_particle.location = particle.location
    
    return new_particle


def create_basic_motion_keyframes(slice, source_emitter):
    
    # Set Final Location Keyframe
    start_frame = RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH
    for particle in slice:
        insert_location_keyframe(particle, start_frame, (particle.location.x, particle.location.y, particle.location.z))
    
    # Set Start Location Keyframe
    end_frame = RING_ANIMATION_START
    random_range = int(ASSEMBLY_START_VARIATION * 30)
    for particle in slice:
        x_variation = 0
        y_variation = 0
        z_variation = 0
        if random_range != 0:
            x_variation = randrange(-random_range, random_range) / 30
            y_variation = randrange(-random_range, random_range) / 30
            z_variation = randrange(-random_range, random_range) / 30
        x_distance = particle.location.x - source_emitter.location.x
        x_pos_sign = 1
        if x_distance != 0:
            x_pos_sign = (x_distance) / abs(x_distance)
        y_distance = particle.location.y - source_emitter.location.y
        y_pos_sign = 1
        if y_distance != 0:
            y_pos_sign = (y_distance) / abs(y_distance)
        z_distance = particle.location.z - source_emitter.location.z
        z_pos_sign = 1
        if z_distance != 0:
            z_pos_sign = (z_distance) / abs(z_distance)
        x_pos = ((particle.location.x - source_emitter.location.x) * ASSEMBLY_TRAVEL_DISTANCE) + source_emitter.location.x + x_variation
        y_pos = ((particle.location.y - source_emitter.location.y) * ASSEMBLY_TRAVEL_DISTANCE) + source_emitter.location.y + y_variation
        z_pos = ((particle.location.z - source_emitter.location.z) * ASSEMBLY_TRAVEL_DISTANCE/20) + source_emitter.location.z + z_variation
        insert_location_keyframe(particle, end_frame, (x_pos, y_pos, z_pos))
        

def create_animated_materials(slice):
    for particle in slice:
        
        ### Orb Visibility ###
        
        # Generate Orb Visibility Offset
        orb_visibility_offset = randrange(0, ORB_VISIBILITY_VARIATION + 1)
        
        # Set First Orb Visibility Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + orb_visibility_offset)
        particle[ORB_VISIBILITY] = 0.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(ORB_VISIBILITY))
        
        # Set Second Orb Visibility Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + orb_visibility_offset + (ASSEMBLY_ANIMATION_LENGTH / 10))
        particle[ORB_VISIBILITY] = 1.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(ORB_VISIBILITY))
        
        # Set Third Orb Visibility Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH)
        particle[ORB_VISIBILITY] = 1.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(ORB_VISIBILITY))
        
        # Set Fourth Orb Visibility Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH + ORB_VISIBILITY_TRANSITION_LENGTH)
        particle[ORB_VISIBILITY] = 0.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(ORB_VISIBILITY))
        
        # Duplicate Material For Object (Necessary to Create Material Driver)
        newMaterial = particle.material_slots[ORB_MATERIAL_SLOT_NAME].material.copy()
        particle.material_slots[ORB_MATERIAL_SLOT_NAME].material = newMaterial
        
        # Add Driver For Material & Connect to Property
        driver_path = 'nodes["{0}"].outputs[0].default_value'.format(ORB_VISIBILITY)
        driver = particle.material_slots[newMaterial.name].material.node_tree.driver_add(driver_path)
        driver.driver.expression = "var"
        variable = driver.driver.variables.new()
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = particle
        variable.targets[0].data_path = "[\"{0}\"]".format(ORB_VISIBILITY)
        
        ### Cube Visibility ###
        
        # Set Initial Cube Visibility Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH)
        particle[CUBE_VISIBILITY] = 0.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(CUBE_VISIBILITY))
        
        # Set Final Cube Visibility Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH)
        particle[CUBE_VISIBILITY] = 1.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(CUBE_VISIBILITY))
        
        # Duplicate Material For Object (Necessary to Create Material Driver)
        newMaterial = particle.material_slots[CUBE_MATERIAL_SLOT_NAME].material.copy()
        particle.material_slots[CUBE_MATERIAL_SLOT_NAME].material = newMaterial
        
        # Add Driver For Material & Connect to Property
        driver_path = 'nodes["{0}"].outputs[0].default_value'.format(CUBE_VISIBILITY)
        driver = particle.material_slots[newMaterial.name].material.node_tree.driver_add(driver_path)
        driver.driver.expression = "var"
        variable = driver.driver.variables.new()
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = particle
        variable.targets[0].data_path = "[\"{0}\"]".format(CUBE_VISIBILITY)
        
        ### Cube Brightness ###
        
        # Set Initial Cube Brightness Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH)
        particle[CUBE_BRIGHTNESS] = 18.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(CUBE_BRIGHTNESS))
        
        # Set Final Cube Brightness Keyframe
        bpy.context.scene.frame_set(RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH + CUBE_BRIGHTNESS_TRANSITION_LENGTH)
        particle[CUBE_BRIGHTNESS] = 3.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(CUBE_BRIGHTNESS))
        
        # Duplicate Material For Object (Necessary to Create Material Driver)
        old_material_name = newMaterial.name
        newMaterial = particle.material_slots[old_material_name].material.copy()
        particle.material_slots[old_material_name].material = newMaterial
        
        # Add Driver For Material & Connect to Property
        driver_path = 'nodes["{0}"].outputs[0].default_value'.format(CUBE_BRIGHTNESS)
        driver = particle.material_slots[newMaterial.name].material.node_tree.driver_add(driver_path)
        driver.driver.expression = "var"
        variable = driver.driver.variables.new()
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = particle
        variable.targets[0].data_path = "[\"{0}\"]".format(CUBE_BRIGHTNESS)


def randomize_flight_pattern(slice):
    for particle in slice:
        
        # Determine Variation Frame
        range = .2
        range_start = int(RING_ANIMATION_START + (((1 - range) / 2) * ASSEMBLY_ANIMATION_LENGTH))
        range_end = int((RING_ANIMATION_START + ASSEMBLY_ANIMATION_LENGTH) - (((1 - range) / 2) * ASSEMBLY_ANIMATION_LENGTH))
        frame = randrange(range_start, range_end)
        
        # Determine Variation Position
        random_range = int(ASSEMBLY_FLIGHT_VARIATION * 30)
        x_variation = 0
        y_variation = 0
        z_variation = 0
        if random_range != 0:
            x_variation = randrange(-int(random_range/2), int(random_range/2)) / 30
            y_variation = randrange(-int(random_range/2), int(random_range/2)) / 30
            z_variation = randrange(-random_range, random_range) / 30
        
        # Determine Position
        x_position = particle.location.x
        y_position = particle.location.y
        z_position = particle.location.z
        if not PARTICLE_DRIFT_BEFORE_ASSEMBLY:
            curves = bpy.data.objects[particle.name].animation_data.action.fcurves
            for curve_number, curve in enumerate(curves):
                if curve.data_path == "location":
                    if curve_number == 0:
                        x_position = curve.evaluate(frame)
                    elif curve_number == 1:
                        y_position = curve.evaluate(frame)
                    else:
                        z_position = curve.evaluate(frame)
    
        # Insert Keyframe
        insert_location_keyframe(particle, frame, (x_position + x_variation, y_position + y_variation, z_position + z_variation))
        

def randomize_keyframe_delay(slice):
    for particle in slice:
        curves = particle.animation_data.action.fcurves
        
        # Calculate Delay
        delay = 0
        if ASSEMBLY_RANDOM_VARIATION > 0:
            delay = randrange(0, ASSEMBLY_RANDOM_VARIATION)
        
        # For Each Location or Material Keyframe
        for curve in curves:
            if curve.data_path == "location" \
                or curve.data_path == "[\"{0}\"]".format(ORB_VISIBILITY) \
                or curve.data_path == "[\"{0}\"]".format(CUBE_VISIBILITY) \
                or curve.data_path == "[\"{0}\"]".format(CUBE_BRIGHTNESS):
                for keyframe_point in curve.keyframe_points:
                    
                    # Advance By Offset
                    keyframe_point.co.x = keyframe_point.co.x + delay
                    keyframe_point.handle_left.x = keyframe_point.handle_left.x + delay
                    keyframe_point.handle_right.x = keyframe_point.handle_right.x + delay
                    
def ease_keyframes(slice):
    for particle in slice:
        for curve in particle.animation_data.action.fcurves:
            if curve.data_path == "location":
                for keyframe_point in curve.keyframe_points:
                    keyframe_point.interpolation = "BEZIER"
    

def remove_easing_on_start_frame(slice):
    for particle in slice:
        curves = particle.animation_data.action.fcurves
        for curve in curves:
            if curve.data_path == "location":
                curve.keyframe_points[0].handle_right = curve.keyframe_points[0].co


def duplicate_slice(slice, source_empty):
    
    # Create Duplicate Empty
    empty = source_empty.copy()
    
    # Parent Empty to Particles
    new_particles = []
    for particle in slice:
        
        # Create Duplicate Particle
        new_particle = particle.copy()
        new_particle.data = particle.data.copy()
        
        # Copy Animations
        action_copy = particle.animation_data.action.copy()
        new_particle.animation_data_create()
        new_particle.animation_data.action = action_copy
        
        # Set Particle Parent
        new_particle.parent = empty
        new_particle.matrix_parent_inverse = empty.matrix_world.inverted()
        
        new_particles.append(new_particle)
    
    return (empty, new_particles)


def rotate_slice_by_angle(empty, angle_vector):
    euler = mathutils.Euler(angle_vector, 'XYZ')

    if empty.rotation_mode == "QUATERNION":
        empty.rotation_quaternion = euler.to_quaternion()
    elif empty.rotation_mode == "AXIS_ANGLE":
        quaternion = euler.to_quaternion()
        empty.rotation_axis_angle[0]  = quaternion.angle
        empty.rotation_axis_angle[1:] = quaternion.axis
    else:
        empty.rotation_euler = euler if euler.order ==empty.rotation_mode else(
            euler.to_quaternion().to_euler(empty.rotation_mode))
            

def offset_animations(slice, offset):
    for particle in slice:
        curves = particle.animation_data.action.fcurves
        
        # For Each Location or Material Keyframe
        for curve in curves:
            if curve.data_path == "location" \
                or curve.data_path == "[\"{0}\"]".format(ORB_VISIBILITY) \
                or curve.data_path == "[\"{0}\"]".format(CUBE_VISIBILITY) \
                or curve.data_path == "[\"{0}\"]".format(CUBE_BRIGHTNESS):
                for keyframe_point in curve.keyframe_points:
                    
                    # Advance By Offset
                    keyframe_point.co.x = keyframe_point.co.x + offset
                    keyframe_point.handle_left.x = keyframe_point.handle_left.x + offset
                    keyframe_point.handle_right.x = keyframe_point.handle_right.x + offset


def hide_object(object):
    bpy.data.objects[object.name].hide_viewport = True
    
    
def get_offset_for_slice(angle):
    # Equation generated by plugging many points on "Animation Progress Marker" rotation
    # curve into free regression curve fitting website MyCurvefit.com and solving the
    # resulting equation for x via WolframAlpha. The resulting equation determines the
    # frame offset of a slice for a given angle (0-180).
    return ((-(-4715661497503125 * angle - 4030738072695250)/(48868807743 - 201647250 * angle)) ** 0.4614561803518418)


### Main Program ###

def main():
   
    # Get Emitter
    source_emitter = bpy.data.objects[EMITTER_NAME]
    
    # Get Selected Slice Particles
    source_particles = []
    for o in bpy.context.selected_objects:
        if o.name != EMITTER_NAME:
            source_particles.append(o)
    
    # Create Final Object List
    object_list = []
    
    # Create Source Empty
    source_empty = bpy.data.objects.new("ParticleEmpty.{:03d}".format(0), None)
    
    # Calculate Slice Animation Offsets
    start_animation_length = 107 + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH
    step_offsets = []
    for sample in range(0, RING_SAMPLES):
        angle = (180 / (RING_SLICES / 2)) * sample
        step_offsets.append(get_offset_for_slice(angle) - start_animation_length)
    
    # For Each Sample (Number of Slices to Generate)
    for sample in range(0, RING_SAMPLES):
    
        # Create New Slice
        new_slice_particles = []
        for particle in source_particles:
            new_slice_particles.append(duplicate_particle(particle))
        
        # Configure New Slice
        create_basic_motion_keyframes(new_slice_particles, source_emitter)
        #create_animated_materials(new_slice_particles)
        randomize_flight_pattern(new_slice_particles)
        randomize_keyframe_delay(new_slice_particles)
        offset_animations(new_slice_particles, step_offsets[sample])
        ease_keyframes(new_slice_particles)
        remove_easing_on_start_frame(new_slice_particles)
        
        # Create Slice Empty
        empty = source_empty.copy()
        
        # Parent Empty to Particles
        for particle in new_slice_particles:
            particle.parent = empty
            particle.matrix_parent_inverse = empty.matrix_world.inverted()
        
        # Determine Rotation Angle
        angle = SLICE_ANGLE * sample
        
        # Rotate Empty
        if sample == 0:
            print("")
        elif sample == (RING_SLICES / 2):
            rotate_slice_by_angle(empty, (0.0, 0.0, math.radians(180)))
        else:
            duplicate_slice_empty, duplicate_slice_particles = duplicate_slice(new_slice_particles, source_empty)
            rotate_slice_by_angle(empty, (0.0, 0.0, math.radians(angle)))
            rotate_slice_by_angle(duplicate_slice_empty, (math.radians(180), 0.0, -math.radians(angle)))
            
            # Add Duplicate Slice to Object List
            object_list.append(duplicate_slice_empty)
            for particle in duplicate_slice_particles:
                object_list.append(particle)
            
        # Print Update
        if OUTPUT_SLICE_PROGRESS:
            print("Slice {0} of {1} processed.".format(sample + 1, RING_SAMPLES))
            
        # Add Slice to Object List
        object_list.append(empty)
        for particle in new_slice_particles:
            object_list.append(particle)
    
    # Create All Objects
    for index, object in enumerate(object_list):
        if OUTPUT_SLICE_PROGRESS:
            print("Object {0} of {1} added to scene.".format(index + 1, len(object_list)))
        bpy.context.collection.objects.link(object)
        hide_object(object)
    
    # Return to Start Frame
    bpy.context.scene.frame_set(RING_ANIMATION_START)
    

if __name__ == '__main__':
    main()