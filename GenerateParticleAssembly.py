import bpy
from random import randrange

# File:             GenerateParticleAssembly.py
# Date:             08.25.2019
# Version:          Blender 2.8
#
# This script creates a "particle" object for each vertex of an "emitter" object and
# animates the particles such that the emitter is randomly assembled. Written as a proof
# of concept for a full HD recreation of Halo 3's loading screen, the script also
# navigates around Blender's arcane API to allow for keyframed material variables. :)
#
# Instructions:
#   1. Model emitter object w/ vertices at desired particle locations.
#   2. Model particle object.
#   3. Name "Particle" and "Emitter" objects accordingly.
#   4. Give particle object a material that includes a single "Value" node. Make sure the node is named
#      according to the MATERIAL_VARIABLE variable below.
#   5. (Optional) Select a collection in the Outliner view for resulting animated objects.
#   6. Run script!


PARTICLE_NAME = "Particle"
EMITTER_NAME = "Emitter"

MATERIAL_VARIABLE = "visibility"

START_FRAME = 0
ASSEMBLY_ANIMATION_LENGTH = 80 # Number of Frames
ASSEMBLY_RANDOM_VARIATION = 120 # Number of Frames
ASSEMBLY_TRAVEL_DISTANCE = 25 # Multiple of Initial Distance
ASSEMBLY_START_VARIATION = 2 # Distance in Blender Units
ASSEMBLY_FLIGHT_VARIATION = 4 # Must be Even


def create_particle_at_vertex(source_particle, vertex):
    
    # Create Particle Object
    new_particle = bpy.data.objects.new(
        name=(source_particle.name+".{:03d}").format(0),
        object_data=source_particle.data.copy()
    )
        
    # Position Object At Vertex
    new_particle.location = vertex.co
    
    # Add Object to Scene
    bpy.context.collection.objects.link(new_particle)
    
    return new_particle


def create_basic_motion_keyframes(new_particles, source_particle):
    
    # Set Final Location Keyframe
    bpy.context.scene.frame_set(START_FRAME + ASSEMBLY_ANIMATION_LENGTH)
    for particle in new_particles:
        particle.keyframe_insert("location")
    
    # Set Start Location Keyframe
    bpy.context.scene.frame_set(START_FRAME)
    for particle in new_particles:
        x_variation = randrange(-ASSEMBLY_START_VARIATION, ASSEMBLY_START_VARIATION)
        y_variation = randrange(-ASSEMBLY_START_VARIATION, ASSEMBLY_START_VARIATION)
        z_variation = randrange(-ASSEMBLY_START_VARIATION, ASSEMBLY_START_VARIATION)
        x_pos = (particle.location.x - source_particle.location.x) * ASSEMBLY_TRAVEL_DISTANCE + x_variation
        y_pos = (particle.location.y - source_particle.location.y) * ASSEMBLY_TRAVEL_DISTANCE + y_variation
        z_pos = (particle.location.z - source_particle.location.z) * ASSEMBLY_TRAVEL_DISTANCE + z_variation
        particle.location.x = x_pos
        particle.location.y = y_pos
        particle.location.z = z_pos
        particle.keyframe_insert("location")
        

def create_animated_material_input(new_particles):
    for particle in new_particles:
        
        # Set Initial Material Property Keyframe
        bpy.context.scene.frame_set(START_FRAME)
        particle[MATERIAL_VARIABLE] = 0.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(MATERIAL_VARIABLE))
        
        # Set Final Material Property Keyframe
        bpy.context.scene.frame_set(START_FRAME + (ASSEMBLY_ANIMATION_LENGTH / 10))
        particle[MATERIAL_VARIABLE] = 1.0
        particle.keyframe_insert(data_path="[\"{0}\"]".format(MATERIAL_VARIABLE))
        
        # Duplicate Material For Object (Necessary to Create Material Driver)
        newMaterial = particle.material_slots[0].material.copy()
        particle.material_slots[0].material = newMaterial
        
        # Add Driver For Material & Connect to Property
        driver_path = 'nodes["{0}"].outputs[0].default_value'.format(MATERIAL_VARIABLE)
        driver = particle.material_slots[0].material.node_tree.driver_add(driver_path)
        driver.driver.expression = "var"
        variable = driver.driver.variables.new()
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = particle
        variable.targets[0].data_path = "[\"{0}\"]".format(MATERIAL_VARIABLE)
        
        
def get_height_factors(new_particles, source_particle):
    raw_height_factors = []
    normalized_height_factors = []
    max_height_factor = 0
    
    # Calculate Raw Height Factors
    for particle in new_particles:
        x_distance = abs(particle.location.x - source_particle.location.x)
        y_distance = abs(particle.location.y - source_particle.location.y)
        if x_distance > y_distance:
            width = x_distance
        else:
            width = y_distance
        if width == 0:
            width = .001
        factor = abs(particle.location.z - source_particle.location.z) / width
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


def give_start_frame_horizontal_bias(new_particles, source_particle):
    bpy.context.scene.frame_set(START_FRAME)
    height_factors = get_height_factors(new_particles, source_particle)
    
    # Update Start Position
    for index, particle in enumerate(new_particles):
        factor = height_factors[index]
        if factor != 0:
            particle.location.x = particle.location.x * (1 + (5 * factor))
            particle.location.y = particle.location.y * (1 + (5 * factor))
            particle.location.z = particle.location.z * .4
            particle.keyframe_insert("location")


def randomize_flight_pattern(new_particles):
    for particle in new_particles:
        
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
        

def randomize_keyframe_delay(new_particles):
    for particle in new_particles:
        curves = particle.animation_data.action.fcurves
        
        # Calculate Delay
        delay = randrange(0, ASSEMBLY_RANDOM_VARIATION)
        
        # For Each Location Keyframe
        for curve in curves:
            if curve.data_path == "location" or curve.data_path == "[\"{0}\"]".format(MATERIAL_VARIABLE):
                for keyframe_point in curve.keyframe_points:
                    
                    # Advance By Offset
                    keyframe_point.co.x = keyframe_point.co.x + delay
                    keyframe_point.handle_left.x = keyframe_point.handle_left.x + delay
                    keyframe_point.handle_right.x = keyframe_point.handle_right.x + delay
                    
def ease_keyframes(new_particles):
    for particle in new_particles:
        for curve in particle.animation_data.action.fcurves:
            if curve.data_path == "location":
                for keyframe_point in curve.keyframe_points:
                    keyframe_point.interpolation = "BEZIER"
    

def remove_easing_on_start_frame(new_particles):
    for particle in new_particles:
        curves = particle.animation_data.action.fcurves
        for curve in curves:
            if curve.data_path == "location":
                curve.keyframe_points[0].handle_right = curve.keyframe_points[0].co


# Main Program
def main():
   
    # Declare Local Variables
    source_particle = bpy.data.objects[PARTICLE_NAME]
    source_emitter = bpy.data.objects[EMITTER_NAME]
    new_particles = []
    
    # Create Particles
    for vertex in source_emitter.data.vertices:
        new_particles.append(create_particle_at_vertex(source_particle, vertex))
    
    # Animate New Particles
    create_basic_motion_keyframes(new_particles, source_particle)
    create_animated_material_input(new_particles)
    give_start_frame_horizontal_bias(new_particles, source_particle)
    randomize_flight_pattern(new_particles)
    randomize_keyframe_delay(new_particles)
    ease_keyframes(new_particles)
    remove_easing_on_start_frame(new_particles)
    
    # Return to Start Frame
    bpy.context.scene.frame_set(START_FRAME)
    

if __name__ == '__main__':
    main()