import os
import re
import bpy

def get_media_duration(image):
    if image.source == 'SEQUENCE':
        # Decompose the filepath according to the naming convention
        dirname, basename = os.path.dirname(image.filepath), os.path.basename(image.filepath)
        prefix, ext = os.path.splitext(basename)
        m = re.match(r"(.*?)(\d+)$", prefix)
        if not m:
            return 1
        base, digits = m.groups()
        num_len = len(digits)
    
        # Find all files belonging to the same sequence
        pattern = re.compile(rf"^{re.escape(base)}(\d{{{num_len}}}){re.escape(ext)}$")
        frames = []
        for f in os.listdir(dirname):
            if pattern.match(f):
                frames.append(int(pattern.match(f).group(1)))
        if frames:
            return max(frames) - min(frames) + 1
        else:
            return 1
        
    elif image.source == 'MOVIE':
        return image.frame_duration
    return 1

def get_media_fps(image):
    scene_fps = bpy.context.scene.render.fps
    scene_fps /= bpy.context.scene.render.fps_base
    
    if image.source != 'MOVIE':
        return scene_fps
    
    try:
        clip = bpy.data.movieclips.load(filepath=image.filepath)
        res = clip.fps
        bpy.data.movieclips.remove(clip)
        return res
    except:
        return scene_fps
    
        