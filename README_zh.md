# Texture VFX Control: Blender Add-on

[[English]](README.md) | [[中文]](README_zh.md)

此Blender插件作用于图像序列或视频纹理节点，将一些原本要在合成器或视频编辑器中才能使用的功能实现在着色器的节点组中，以便直接在三维空间中进行影片合成。

本插件的功能包括：

- 用关键帧控制视频纹理的播放
  - 变速/倒放/延时等效果均可实现
- 视频特效节点组
  - 模糊
  - 色键抠像
  - 描边


## 系统需求

Blender 3.3以上（包括Blender 4.0）

## 安装步骤

1. [下载](https://github.com/chsh2/texture_vfx_control/releases)`.zip`压缩包。
2. 在`[偏好设置] > [插件]`面板中安装并启用本插件。

![](docs/install.png)

## 使用步骤

建议将本插件与Blender自带的[Images as Planes](https://docs.blender.org/manual/en/latest/addons/import_export/images_as_planes.html)插件一同使用。用后者导入图像或视频后，可在菜单`[物体] > [快速效果] > [Texture VFX Control]`中使用本插件的功能。

![](docs/menu.png)

此外，本插件也可用于任一含有图像纹理节点的材质。如果该材质含有多个图像纹理，需要在着色器编辑器中选择想要处理的纹理。在着色器编辑器窗口的`[添加]`菜单中也能找到本插件的功能入口。

### 播放进度控制

![](docs/playback.png)

`[Add Texture Playback Driver]`菜单选项将[驱动器](https://docs.blender.org/manual/en/latest/animation/drivers/introduction.html)添加到图像序列/视频的`偏移量`属性上。同时，一个名为`playhead_{{视频文件名}}`的新的自定义属性会出现在`物体属性`面板中。

为这个自定义属性添加关键帧即可控制视频播放。它的取值在0~1之间，分别对应视频的第一帧与最后一帧。除手动添加关键帧外，插件也提供了一些预置选项，如变速播放、倒放、循环播放等。

**[!局限!]** *视频的偏移量属于材质属性的一部分，因此所有拥有此材质的物体都会显示同一帧视频，而无法设定不同的播放进度。如果想要在多个物体上播放相同的视频，且拥有不同的播放进度，建议用[Images as Planes](https://docs.blender.org/manual/en/latest/addons/import_export/images_as_planes.html)重新导入视频素材，而不是复制已经被导入的物体。*

### 特效节点组

![](docs/fx.png)

名为`[Effect: *]`的菜单选项可为图像/视频纹理添加特效。一个纹理可以添加多个特效，这些特效也可以与前面的播放进度控制功能一起使用。

如果想要手动连接节点来实现更丰富的效果，`[Append VFX Node Groups]`菜单选项可以将所有插件预置的节点组追加导入到当前的文件中。

**[!局限!]** *描边节点的设置较为复杂，且必须将纹理节点复制4份以实现边缘检测。如果要将该节点与本插件以外的节点组混合使用，请务必注意节点的连接方式与顺序是否正确。*

## 参考与致谢

The method of Chroma Key comes from [OBS Studio](https://obsproject.com/). Its implementation also refers to a [Godot shader](https://godotshaders.com/shader/green-screen-chromakey/) made by [BlueMoon_Coder](https://godotshaders.com/author/bluemoon_coder/).

The example video used in this document is from [Pixabay](https://pixabay.com/videos/cat-pet-green-screen-green-nature-116648/) made by BoVibol.