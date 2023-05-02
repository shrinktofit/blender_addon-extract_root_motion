# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Extract Root Motion",
    "author" : "Leslie Leigh",
    "category" : "Animation",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
}

operator_id = 'opr.extract_root_motion'

import bpy
from .extract import *

class RootMotionComponentsExtractionSettingsPropertyGroup(bpy.types.PropertyGroup):
    location_x: bpy.props.BoolProperty(name="Location X")
    location_y: bpy.props.BoolProperty(name="Location Y")
    location_z: bpy.props.BoolProperty(name="Location Z")

    scale_x: bpy.props.BoolProperty(name="Scale X")
    scale_y: bpy.props.BoolProperty(name="Scale Y")
    scale_z: bpy.props.BoolProperty(name="Scale Z")

class RootMotionExtractSettingsPropertyGroup(bpy.types.PropertyGroup):
    source_bone_name: bpy.props.StringProperty(name='Source Bone Name', default='')
    target_bone_name: bpy.props.StringProperty(name='Target Bone Name', default='')
    normalize: bpy.props.BoolProperty(name='Normalize', default=True)
    components: bpy.props.PointerProperty(type=RootMotionComponentsExtractionSettingsPropertyGroup, name='Enabled Components')

class ExtractRootMotionOperator(bpy.types.Operator):
    """Extract root motion of an action"""
    bl_idname = operator_id
    bl_label = "Extract Root Motion"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        object = context.object;
        extract(self, object, object.root_motion_extraction_setting)
        return {'FINISHED'}

class ExtractRootMotionPanel(bpy.types.Panel):
    """Extract root motion of an action"""
    bl_category = 'Root Motion'
    bl_idname = "VIEW3D_PT_extract_root_motion"
    bl_label = "Extract Root Motion Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        col = self.layout.column()

        object = bpy.context.object
        if not object:
            if len(bpy.context.selected_objects) != 0:
                object = bpy.context.selected_objects[0]
        
        if not object:
            col.row().label(text='Neither current context has no associated object, nor current no selected object.')
            return
        
        if object.type != 'ARMATURE':
            col.row().label(text='The object %s is not an armature.' % object.name)
            return
        
        settings = object.root_motion_extraction_setting

        col.row().label(text='Object: %s' % object.name)
        col.row().prop_search(settings, 'source_bone_name', object.data, 'bones')
        col.row().prop(settings, 'target_bone_name')
        col.row().prop(settings, 'normalize')

        col.row().separator()

        for prop_name in settings.components.__annotations__.keys():
            col.row().prop(settings.components, prop_name)

        col.row().separator()

        col.operator(operator_id, text='Extract')

register_classes, unregister_classes = bpy.utils.register_classes_factory((
    RootMotionComponentsExtractionSettingsPropertyGroup,
    RootMotionExtractSettingsPropertyGroup,
    ExtractRootMotionOperator,
    ExtractRootMotionPanel,
))

def register():
    print('Register')
    register_classes()
    bpy.types.Object.root_motion_extraction_setting = bpy.props.PointerProperty(type=RootMotionExtractSettingsPropertyGroup, name='Enabled Properties')

def unregister():
    print('Unregistered')
    unregister_classes()
    del bpy.types.Object.root_motion_extraction_setting

if __name__ == '__main__':
    register()

