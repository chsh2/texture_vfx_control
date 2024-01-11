# Texture VFX Control: Blender Add-on

This Blender add-on provides with shader-based effects on image/sequence/movie textures. Users can perform video composition directly in the 3D space without using the compositor or the video sequence editor.

The functionalities of this add-on include:

- Texture Playback Control
  - Controlling the playback and speed of sequence/movie textures with keyframes
- VFX Shaders
  - Blur
  - Chroma Key
  - Outline


## Requirements

Blender 3.3+ or Blender 4.0

## Installation

1. Download the `.zip` archive from the [Releases](https://github.com/chsh2/texture_vfx_control/releases) page.
2. Install and enable the add-on from `[Preferences] > [Add-ons]` panel.

![](docs/install.png)

## Usage

It is recommended to use this add-on's operators on images/sequences/movies imported through [Images as Planes](https://docs.blender.org/manual/en/latest/addons/import_export/images_as_planes.html). Select the imported object, and access the add-on through `[Object] > [Quick Effects] > [Texture VFX Control]`.

![](docs/menu.png)

The add-on can also work with any material containing a [Image Texture](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/image.html) shader node. If the active material contains more than one image texture, please select one of them in the Shader Editor. A similar menu is available in the Shader Editor's `[Add] > [Texture VFX Control]`.

### Playback Control Driver


**[Limitations]**

### VFX Shader Node Groups

**[Limitations]**

## Credits

The method of Chroma Key comes from [OBS Studio](https://obsproject.com/). Its implementation also refers to a [Godot shader](https://godotshaders.com/shader/green-screen-chromakey/) made by [BlueMoon_Coder](https://godotshaders.com/author/bluemoon_coder/).