# Texture VFX Control: Blender Add-on

[[English]](README.md) | [[中文]](README_zh.md)

[<📖Documentation>](https://chsh2.github.io/tfx/) | [<🎥Video Demo>](https://youtu.be/jcMXFulEM1k)

Texture VFX Control is a Blender add-on working on media (videos, images and image sequences) as textures, enabling management of media playback progress and visual effects. The users can have the video editing/composition workflow in the 3D space, therefore facilitating the creation of motion graphics and reels.

![](docs/images/cover.png)

Main features:

- **Media Playback Control**
  - Cropping, speed adjustment and reverse playback controlled by keyframes
  - A workspace for arranging multiple video clips
- **Effects Chain Control**
  - Quick application of over 40 popular video effects
  - Non-destructive editing of multiple effects as a chain
  - Save effects as presets and transfer them between objects

## Requirements

Blender 4.2 - 5.1

## Installation

1. Download the `.zip` archive from the [Releases](https://github.com/chsh2/texture_vfx_control/releases) page.
2. Install and enable the add-on from `[Preferences] > [Add-ons]` panel.

<img src="docs/images/install.png" width=600>

## Usage

The add-on can be called from the sidebar of the 3D viewport. A tab named `TexFX` will appear in the sidebar when the active object material contains at least one [Image Texture Node](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/image.html). The most common way to import media files as textures is through the menu item `[Add] > [Image] > [Mesh Plane]`.

To enable the add-on, click the `[Convert a Texture to FX Node]` button and select the name of the media. After the operation is successful, more panels will appear in the sidebar for subsequent actions.

Please refer to the [online manual](https://chsh2.github.io/tfx/) for more information.

## Credits

The shader node groups in this add-on have the following references:
- https://github.com/obsproject/obs-studio/blob/master/plugins/obs-filters/data/chroma_key_filter.effect
- https://godotshaders.com/shader/green-screen-chromakey/
- https://www.shadertoy.com/view/7sscD4
- https://www.shadertoy.com/view/4s2GRR
- https://www.shadertoy.com/view/ls3cDB

The following assets are used for demonstration purposes in the documentation:
- Adrian Hoparda at [pexels.com](https://www.pexels.com/@adrian-hoparda-1684220/)
- BoVibol, fawaz-qureshi at [pixabay.com](https://pixabay.com/)
- Big Buck Bunny from [Blender Foundation](https://peach.blender.org/)
