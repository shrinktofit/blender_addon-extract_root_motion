import bpy
import numpy as np

# def print(data):
#     for window in bpy.context.window_manager.windows:
#         screen = window.screen
#         for area in screen.areas:
#             if area.type == 'CONSOLE':
#                 override = {'window': window, 'screen': screen, 'area': area}
#                 bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")
                
def process_action(operator, action, settings):
    print('Processing action %s' % action.name)

    source_bone_name = settings.source_bone_name
    target_bone_name = settings.target_bone_name
    components = settings.components
    should_normalize = settings.normalize

    source_bone_fcurve_prefix = 'pose.bones[\"%s\"].' % source_bone_name
    target_bone_fcurve_prefix = 'pose.bones[\"%s\"].' % target_bone_name

    component_extraction_options = [option for option in [
        ('location', 0, 'Location X') if components.location_x else None,
        ('location', 1, 'Location Y') if components.location_y else None,
        ('location', 2, 'Location Z') if components.location_z else None,
    ] if option];
        
    fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
    print('Current FPS: %s' % fps)
    # seconds per frame
    spf = 1.0 / fps

    for _, (data_path, array_index, human_component_name) in enumerate(component_extraction_options):
        print('Extracting %s' % human_component_name)

        source_data_path = '%s%s' % (source_bone_fcurve_prefix, data_path)
        source_fcurve = action.fcurves.find(source_data_path, index=array_index)
        if not source_fcurve:
            operator.report({'WARNING'}, 'The action %s contains no animation for %s %s' % (action.name, source_bone_name, human_component_name))
            continue

        target_data_path = '%s%s' % (target_bone_fcurve_prefix, data_path)
        target_fcurve = action.fcurves.find(target_data_path, index=array_index)
        if target_fcurve:
            print('Remove already axisting target fcurve %s[%d]' % (target_fcurve.data_path, target_fcurve.array_index))
            action.fcurves.remove(target_fcurve)
        target_fcurve = action.fcurves.new(target_data_path, index=array_index)
        
        curve_frame_range = source_fcurve.range()
        print('Process %s[%d] -> %s[%d]. Frame range: %d-%d' % (source_fcurve.data_path, source_fcurve.array_index, target_fcurve.data_path, target_fcurve.array_index, curve_frame_range.x, curve_frame_range.y))
        
        times = []
        values = []
        min_v = float('inf')
        max_v = float('-inf')
        for i_frame, frame in enumerate(np.arange(curve_frame_range.x, curve_frame_range.y, 1)):
            times.append(frame)
            v = source_fcurve.evaluate(frame)
            values.append(v)
            min_v = min(min_v, v)
            max_v = max(max_v, v)

        # Normalize values to [0, 1].
        if should_normalize:
            values = [v / (max_v - min_v) for v in values]
            
        # Absolute values to delta values(change per seconds).
        values = [0 if i_frame == 0 else (values[i_frame] - values[i_frame - 1]) / spf for i_frame, v in enumerate(values)]
        
        for i_frame in range(len(times)):
            target_fcurve.keyframe_points.insert(times[i_frame], values[i_frame], options={'FAST'})
            
def extract(operator, obj, settings):
    print('Starting extraction.')

    if obj.type != 'ARMATURE':
        print('The object is not an armature.')
        return
    
    armature = obj.data;
    print('Processing armature %s' % obj.name)
    
    if not settings.source_bone_name:
        operator.report({'ERROR'}, 'Source bone is not specified.')
        return
    
    if not settings.target_bone_name:
        operator.report({'ERROR'}, 'Target bone is not specified.')
        return

    if armature.bones.find(settings.source_bone_name) < 0:
        operator.report({'ERROR'}, 'Source bone %s does not exists.' % settings.source_bone_name)
        return
    
    actions = []
    animation_data = obj.animation_data
    if animation_data:
        if animation_data.action:
            actions.append(animation_data.action)

    if len(actions) == 0:
        operator.report({'WARNING'}, 'There\'s no activated action on this object')
        return

    if armature.bones.find(settings.target_bone_name) < 0:
        print('Target bone %s does not exists. A new one would be created.' % settings.target_bone_name)
        
        current_mode = bpy.context.object.mode
        
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        target_bone = armature.edit_bones.new(settings.target_bone_name)
        target_bone.head = (0, 0, 0)
        target_bone.tail = (0, 0, 1)
        
        bpy.ops.object.mode_set(mode=current_mode, toggle=False)

    for action in actions:
        process_action(operator, action, settings)
