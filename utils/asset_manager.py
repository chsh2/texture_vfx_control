import bpy
import uuid
import os

basic_template_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../resources/templates/basic.blend')
template_fx_list = [
    {"category": "Color", "effects": [
        {"name": "Invert", "file": basic_template_filepath, "node_name": "invert"},
        {"name": "HSV", "file": basic_template_filepath, "node_name": "hsv"},
        {"name": "Brightness / Contrast", "file": basic_template_filepath, "node_name": "brightness_contrast"},
        {"name": "RGB Curves", "file": basic_template_filepath, "node_name": "rgb_curves"},
        {"name": "Gradient Map", "file": basic_template_filepath, "node_name": "gradient_map"},
        {"name": "Linear Gradient", "file": basic_template_filepath, "node_name": "linear_gradient"},
        {"name": "Color Quantization", "file": basic_template_filepath, "node_name": "color_quantization"},]
    },
    {"category": "Alpha", "effects": [
        {"name": "Chroma Key", "file": basic_template_filepath, "node_name": "chroma_key"},
        {"name": "Alpha Choker", "file": basic_template_filepath, "node_name": "alpha_choker"},
        {"name": "Alpha Clip", "file": basic_template_filepath, "node_name": "alpha_clip"},]
    },
    {"category": "Blur/Enhancement", "effects": [
        {"name": "Grainy Blur", "file": basic_template_filepath, "node_name": "grainy_blur"},
        {"name": "Sharpen", "file": basic_template_filepath, "node_name": "sharpen"},
        {"name": "Outline", "file": basic_template_filepath, "node_name": "outline"},
        {"name": "Rim Light / Shadow", "file": basic_template_filepath, "node_name": "rim_light"},]
    },
    {"category": "Distortion", "effects": [
        {"name": "Fisheye", "file": basic_template_filepath, "node_name": "fisheye"},
        {"name": "Swirl", "file": basic_template_filepath, "node_name": "swirl"},]
    },
    {"category": "Stylization", "effects": [
        {"name": "Pixelate", "file": basic_template_filepath, "node_name": "pixelate"},
        {"name": "Vignette", "file": basic_template_filepath, "node_name": "vignette"},
        {"name": "Halftone", "file": basic_template_filepath, "node_name": "halftone"},
        {"name": "RGB Split", "file": basic_template_filepath, "node_name": "rgb_split"},]
    },
    {"category": "Simulation", "effects": [
        {"name": "LCD", "file": basic_template_filepath, "node_name": "lcd"},]
    },
    {"category": "Transition", "effects": [
        {"name": "Fade", "file": basic_template_filepath, "node_name": "fade"},
        {"name": "Tile", "file": basic_template_filepath, "node_name": "tile"},
        {"name": "Clock Wipe", "file": basic_template_filepath, "node_name": "clock_wipe"},]
    },
]

def create_node_group_instance(template_filepath=None, group_name=''):
    """
    Create a new node group by appending from a template blend file
    """
    if template_filepath is None:
        template_filepath = basic_template_filepath
    
    # Append the node group from the template blend file
    with bpy.data.libraries.load(template_filepath, link=False) as (data_from, data_to):
        if group_name in data_from.node_groups:
            data_to.node_groups.append(group_name)
        else:
            raise ValueError(f"Node group '{group_name}' not found in {template_filepath}")
    
    # Randomly generate a suffix to the node group name
    new_group = data_to.node_groups[0]
    new_group.name = f"{group_name}_{str(uuid.uuid4())[:8]}"

    return new_group