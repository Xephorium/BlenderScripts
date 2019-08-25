import bpy
import math
import mathutils
from random import randrange

# File:             GenerateHaloRing.py
# Date:             08.25.2019
# Version:          Blender 2.8
#
# This script duplicates one slice of a Halo ring consisting of many individual cube objects, keyframes
# location and material animations for each object, parents the new objects to an empty, and rotates the empty into
# position. Run with care; this one's a computational behemoth.
#
# Instructions (Out of date):
#   1. Model emitter object w/ vertices at desired particle locations.
#   2. Model particle object.
#   3. Name "Particle" and "Emitter" objects accordingly.
#   4. Give particle object a material that includes a single "Value" node. Make sure the node is named
#      according to the MATERIAL_VARIABLE variable below.
#   5. (Optional) Select a collection in the Outliner view for resulting animated objects.
#   6. Run script!


EMITTER_NAME = "Emitter"

START_FRAME = 0
ASSEMBLY_ANIMATION_LENGTH = 80 # Number of Frames
ASSEMBLY_RANDOM_VARIATION = 120 # Number of Frames
ASSEMBLY_TRAVEL_DISTANCE = 25 # Multiple of Initial Distance
ASSEMBLY_START_VARIATION = 2 # Distance in Blender Units
ASSEMBLY_FLIGHT_VARIATION = 4 # Must be Even

ORB_VISIBILITY = "Orb Visibility"
CUBE_VISIBILITY = "Cube Visibility"
CUBE_BRIGHTNESS = "Cube Brightness"
ORB_MATERIAL_SLOT_NAME = "Orb Material"
CUBE_MATERIAL_SLOT_NAME = "Cube Material"
CUBE_VISIBILITY_TRANSITION_LENGTH = 20 # Number of Frames
CUBE_BRIGHTNESS_TRANSITION_LENGTH = 120 # Number of Frames

RING_SLICES = 256
RING_SAMPLES = 3 # Number of Slices to Generate
SLICE_ANGLE = 360 / RING_SLICES


def duplicate_particle(particle):
    
    # Create Particle Object
    new_particle = bpy.data.objects.new(
        name=(particle.name+".{:03d}").format(0),
        object_data=particle.data.copy()
    )
        
    # Position Object At Vertex
    new_particle.location = particle.location
    
    # Add Object to Scene
    bpy.context.collection.objects.link(new_particle)
    
    return new_particle


def create_basic_motion_keyframes(slice, source_emitter):
    
    # Set Final Location Keyframe
    bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH)
    for particle in slice:
        particle.keyframe_insert("location")
    
    # Set Start Location Keyframe
    bpy.context.scene.frame_set(START_FRAME)
    for particle in slice:
        x_variation = randrange(-ASSEMBLY_START_VARIATION, ASSEMBLY_START_VARIATION)
        y_variation = randrange(-ASSEMBLY_START_VARIATION, ASSEMBLY_START_VARIATION)
        z_variation = randrange(-ASSEMBLY_START_VARIATION, ASSEMBLY_START_VARIATION)
        x_pos = (particle.location.x - source_emitter.location.x) * ASSEMBLY_TRAVEL_DISTANCE + x_variation
        y_pos = (particle.location.y - source_emitter.location.y) * ASSEMBLY_TRAVEL_DISTANCE + y_variation
        z_pos = (particle.location.z - source_emitter.location.z) * ASSEMBLY_TRAVEL_DISTANCE + z_variation
        particle.location.x = x_pos
        particle.location.y = y_pos
        particle.location.z = z_pos
        particle.keyframe_insert("location")
        

def create_animated_materials(slice):
    for particle in slice:
        
        ### Orb Visibility ###
        
        # Set First Orb Visibility Keyframe
        bpy.context.scene.frame_set(START_FRAME)
        particle[ORB_VISIBILITY] = 0.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(ORB_VISIBILITY))
        
        # Set Second Orb Visibility Keyframe
        bpy.context.scene.frame_set(START_FRAME + (ASSEMBLY_ANIMATION_LENGTH / 10))
        particle[ORB_VISIBILITY] = 1.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(ORB_VISIBILITY))
        
        # Set Third Orb Visibility Keyframe
        bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH)
        particle[ORB_VISIBILITY] = 1.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(ORB_VISIBILITY))
        
        # Set Fourth Orb Visibility Keyframe
        bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH)
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
        bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH)
        particle[CUBE_VISIBILITY] = 0.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(CUBE_VISIBILITY))
        
        # Set Final Cube Visibility Keyframe
        bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH)
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
        bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH)
        particle[CUBE_BRIGHTNESS] = 3.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(CUBE_BRIGHTNESS))
        
        # Set Final Cube Brightness Keyframe
        bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH + CUBE_VISIBILITY_TRANSITION_LENGTH + CUBE_BRIGHTNESS_TRANSITION_LENGTH)
        particle[CUBE_BRIGHTNESS] = 1.0
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
        
        
def get_height_factors(slice, source_emitter):
    raw_height_factors = []
    normalized_height_factors = []
    max_height_factor = 0
    
    # Calculate Raw Height Factors
    for particle in slice:
        x_distance = abs(particle.location.x - source_emitter.location.x)
        y_distance = abs(particle.location.y - source_emitter.location.y)
        if x_distance > y_distance:
            width = x_distance
        else:
            width = y_distance
        if width == 0:
            width = .001
        factor = abs(particle.location.z - source_emitter.location.z) / width
        raw_height_factors.append(factor)
        if factor > max_height_factor:
            max_height_factor = factor
        
    # Normalize Height Factors
    for factor in raw_height_factors:
        if factor > 0:
            new_factor = factor/max_height_factor
        else:
            new_factor = 0
        normalized_height_factors.append(new_factor)
    
    return normalized_height_factors


def give_start_frame_horizontal_bias(slice, source_emitter):
    bpy.context.scene.frame_set(START_FRAME)
    height_factors = get_height_factors(slice, source_emitter)
    
    # Update Start Position
    for index, particle in enumerate(slice):
        factor = height_factors[index]
        if factor != 0:
            particle.location.x = particle.location.x * (1 + (5 * factor))
            particle.location.y = particle.location.y * (1 + (5 * factor))
            particle.location.z = particle.location.z * .4
            particle.keyframe_insert("location")


def randomize_flight_pattern(slice):
    for particle in slice:
        
        # Determine Flight Variation
        x_variation = randrange(-ASSEMBLY_FLIGHT_VARIATION, ASSEMBLY_FLIGHT_VARIATION)
        y_variation = randrange(-ASSEMBLY_FLIGHT_VARIATION, ASSEMBLY_FLIGHT_VARIATION)
        z_variation = randrange(-(ASSEMBLY_FLIGHT_VARIATION/2), (ASSEMBLY_FLIGHT_VARIATION/2))
        
        # Determine Variation Frame
        range = .2
        range_start = int(START_FRAME + (((1 - range) / 2) * ASSEMBLY_ANIMATION_LENGTH))
        range_end = int((START_FRAME + ASSEMBLY_ANIMATION_LENGTH) - (((1 - range) / 2) * ASSEMBLY_ANIMATION_LENGTH))
        frame = randrange(range_start, range_end)
        
        # Randomize Flight Path
        bpy.context.scene.frame_set(frame)
        particle.location.x = particle.location.x + x_variation
        particle.location.y = particle.location.y + y_variation
        particle.location.z = particle.location.z + z_variation
        
        # Insert Keyframe
        particle.keyframe_insert("location")
        

def randomize_keyframe_delay(slice):
    for particle in slice:
        curves = particle.animation_data.action.fcurves
        
        # Calculate Delay
        delay = randrange(0, ASSEMBLY_RANDOM_VARIATION)
        
        # For Each Location Keyframe
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


def duplicate_slice(slice):
    
    # Create Duplicate Empty
    empty = bpy.data.objects.new("ParticleEmpty.{:03d}".format(0), None)
    bpy.context.collection.objects.link(empty)
    
    # Parent Empty to Particles
    for particle in slice:
        
        # Create Duplicate Particle
        new_particle = bpy.data.objects.new(
            name=(particle.name+".{:03d}").format(0),
            object_data=particle.data.copy()
        )
        bpy.context.collection.objects.link(new_particle)
        
        # Copy Animations
        action_copy = particle.animation_data.action.copy()
        new_particle.animation_data_create()
        new_particle.animation_data.action = action_copy
        
        # Set Particle Parent
        new_particle.parent = empty
        new_particle.matrix_parent_inverse = empty.matrix_world.inverted()
    
    return empty


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


# Main Program
def main():
   
    # Get Emitter
    source_emitter = bpy.data.objects[EMITTER_NAME]
    
    # Get Selected Slice Particles
    source_particles = []
    for o in bpy.context.selected_objects:
        if o.name != EMITTER_NAME:
            source_particles.append(o)
    
    # For Each Sample (Number of Slices to Generate)
    for sample in range(0, RING_SAMPLES):
    
        # Create New Slice
        new_slice_particles = []
        for particle in source_particles:
            new_slice_particles.append(duplicate_particle(particle))
        
        # Configure New Slice
        create_basic_motion_keyframes(new_slice_particles, source_emitter)
        create_animated_materials(new_slice_particles)
        give_start_frame_horizontal_bias(new_slice_particles, source_emitter)
        randomize_flight_pattern(new_slice_particles)
        randomize_keyframe_delay(new_slice_particles)
        ease_keyframes(new_slice_particles)
        remove_easing_on_start_frame(new_slice_particles)
        
        # Create Slice Empty
        empty = bpy.data.objects.new("ParticleEmpty.{:03d}".format(0), None)
        bpy.context.collection.objects.link(empty)
        
        # Parent Empty to Particles
        for particle in new_slice_particles:
            particle.parent = empty
            particle.matrix_parent_inverse = empty.matrix_world.inverted()
        
        # Determine Rotation Angle
        angle = SLICE_ANGLE * sample
        
        # Rotate Empty
        if sample == 0:
            print("Do Nothing - Slice In Position")
        elif sample == (RING_SLICES / 2) - 1:
            rotate_slice_by_angle(empty, (0.0, 0.0, math.radians(180)))
        else:
            duplicate_slice_empty = duplicate_slice(new_slice_particles)
            rotate_slice_by_angle(empty, (0.0, 0.0, math.radians(angle)))
            rotate_slice_by_angle(duplicate_slice_empty, (math.radians(180), 0.0, -math.radians(angle)))
            
    
    # Return to Start Frame
    bpy.context.scene.frame_set(START_FRAME)
    

if __name__ == '__main__':
    main()