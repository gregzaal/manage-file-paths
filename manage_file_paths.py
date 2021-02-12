# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Manage File Paths",
    "description": "Lists file paths for images and caches, showing broken paths, and allowing Find & Replace in paths.",
    "author": "Greg Zaal",
    "version": (0, 3),
    "blender": (2, 91, 0),
    "location": "Properties Editor > Scene > File Paths panel",
    "warning": "",
    "wiki_url": "https://github.com/gregzaal/manage-file-paths",
    "tracker_url": "https://github.com/gregzaal/manage-file-paths/issues",
    "category": "Scene"}

import bpy
import os
from shutil import copy2 as copyfile

'''
TODOs:
    Don't fetch image list or check for existance on every redraw, make refresh button (and maybe refresh automatically every so often with modal timer?)
    Find and replace individually
    Only if file doesn't exist
    Somehow automatically try fix paths based on history (stored in config)
    Reload images
'''


class MFPProps(bpy.types.PropertyGroup):
    bl_idname = __package__

    source: bpy.props.StringProperty(
        name="Find",
        default="",
        description="source")

    target: bpy.props.StringProperty(
        name="Replace",
        default="",
        description="target")


def get_images():
    images = []
    for i in bpy.data.images:
        if i.source == 'FILE':
            if not i.library:  # ignore linked images since we cannot modify them
                images.append(i)
    return images


def file_exists(path):
    if path.startswith('//'):  # os.path.exists only works with absolute paths
        path = bpy.path.abspath(path)

    return os.path.exists(path)


def all_rel_to_abs():
    images = get_images()
    for img in images:
        if img.filepath.startswith('//'):
            img.filepath = bpy.path.abspath(img.filepath)


class MFP_OT_FindReplace(bpy.types.Operator):
    """Replace the text specified in 'Find' with that in 'Replace'"""
    bl_idname = "mfp.find_replace"
    bl_label = "Find & Replace"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mfp_props
        images = get_images()

        for img in images:
            img.filepath = img.filepath.replace(props.source, props.target)
        return {'FINISHED'}


class MFP_OT_Copy(bpy.types.Operator):
    """Tooltip"""  # TODO
    bl_idname = "mfp.copy"
    bl_label = "Copy Source to Target"

    def execute(self, context):
        all_rel_to_abs()
        props = context.scene.mfp_props
        images = get_images()

        for img in images:
            old_path = img.filepath
            if props.source in old_path:
                new_path = old_path.replace(props.source, props.target)
                new_path_root = os.sep.join(new_path.split(os.sep)[:-1])
                if not os.path.exists(new_path_root):
                    os.makedirs(new_path_root)
                img.filepath = new_path
                copyfile (old_path, new_path)
        return {'FINISHED'}


class MFP_PT_ImagePathsPanel(bpy.types.Panel):
    bl_label = "File Paths"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        images = get_images()
        caches = bpy.data.cache_files
        props = context.scene.mfp_props

        col = layout.column()
        for img in images:
            row = col.row(align=True)
            row.prop(img, 'filepath', text=img.name)
            i = 'BLANK1' if file_exists(img.filepath) else 'LIBRARY_DATA_BROKEN'
            row.label(text='', icon=i)

        if caches:
            col = layout.column()
            for c in caches:
                row = col.row(align=True)
                row.prop(c, 'filepath', text=c.name)
                i = 'BLANK1' if file_exists(c.filepath) else 'LIBRARY_DATA_BROKEN'
                row.label(text='', icon=i)

        col = layout.column(align=True)
        col.operator('file.find_missing_files')
        col.operator('file.make_paths_relative')
        col.operator('outliner.orphans_purge', text="Remove Unused")


class MFP_PT_FindReplace(bpy.types.Panel):
    bl_label = "Find & Replace"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_parent_id = "MFP_PT_ImagePathsPanel"

    def draw(self, context):
        layout = self.layout
        props = context.scene.mfp_props

        col = layout.column(align=True)
        col.prop(props, 'source')
        col.prop(props, 'target')
        col.separator()
        col.operator('mfp.find_replace')


classes = [
    MFPProps,
    MFP_OT_FindReplace,
    MFP_PT_ImagePathsPanel,
    MFP_PT_FindReplace,
]


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.mfp_props = bpy.props.PointerProperty(type=MFPProps)


def unregister():
    del bpy.types.Scene.mfp_props

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
