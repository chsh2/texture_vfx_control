# Texture VFX Control: Blender Add-on

[[English]](README.md) | [[中文]](README_zh.md)

本Blender插件作用于媒体纹理（图片、图片序列和视频），利用节点组和驱动器来实现媒体的播放进度管理和特效管理。用户在三维空间中仍可按照视频编辑/合成软件的习惯进行操作，从而提高动态图形与视频特效的制作效率。

本插件的主要功能如下：

- **媒体播放管理**
  - 视频剪裁/变速/倒放、利用关键帧控制播放进度
  - 用来排列组织多个视频的管理器界面
- **视频特效管理**
  - 一键应用超过30种常见的视频特效/转场
  - 复数特效的链式管理与非破坏性编辑
  - 保存特效作为预置、为多个物体批量应用特效

## 系统需求

Blender 4.2 ~ 5.0

## 安装步骤

1. [下载](https://github.com/chsh2/texture_vfx_control/releases)`.zip`压缩包。
2. 在`[偏好设置] > [插件]`面板中安装并启用本插件。

<img src="docs/install.png" width=600>

## 使用步骤

如果当前物体的材质包含[图像纹理节点](https://docs.blender.org/manual/en/latest/render/shader_nodes/textures/image.html)，3D视图的侧边栏会出现`TexFX`标签，本插件的功能可在该标签页内使用。通常推荐使用Blender内置的`[添加] > [图像] > [网格平面]`菜单项来导入图片或视频。

要启用插件功能，请点击侧边栏中`[Convert a Texture to FX Node]`按钮，并在下拉菜单中选择图像/视频的名称。操作成功后，侧边栏中将出现更多面板，以供进行后续操作。

### 播放管理

播放管理功能适用于视频或图片序列，无法对静态图片使用。使用`[Add Playback Controller]`按钮即可为调节视频的播放速度、循环次数等属性。插件支持两种方式来进行视频管理。

#### 关键帧控制

<img src="docs/playback_keyframes.gif" width=600>

此模式下，材质将被添加名为`tfxPlayhead`的关键帧动画通道，该值为0时对应视频播放开始、为1时对应视频播放结束。用户可利用关键帧与曲线实现视频播放进度的精细控制。

#### 全局管理器

<img src="docs/playback_manager.png" width=600>

此模式下，插件会在场景中创建一个名为`TfxPlaybackManager`的物体，集中管理所有视频播放信息。点击`[Open Global Manager]`按钮可进入一个新工作区，用户可以在其中直观地管理多个视频片段。

### 特效管理

<img src="docs/effects_chain.gif" width=600>

特效管理功能既适用于视频，也适用于静态图片。使用侧边栏最下方`[Effects Chain] > [New Effect]`按钮为媒体插入一个新特效。该面板将显示出目前已经应用在当前媒体上的所有特效，用户可以调节特效的参数，或者关闭/启用/删除任一特效。

#### 驱动器

<img src="docs/effects_driver.gif" width=600>

部分特效参数的数值旁边显示有图标，插件为这些参数设计了驱动器，以快速实现某些视觉效果。典型的驱动器包括：

- **位置驱动**: 与另一个指定物体的相对位置会影响该参数的值。例如投影效果可以通过指定作为光源的物体来自动决定阴影的方向。
- **时间驱动**: 对于动态的视觉效果，设置该驱动器可以让参数的值随视频的帧数自动增长，因此不需要手动设置关键帧即可实现动画。
- **渐入/渐出**: 对于过渡特效，如果媒体已经使用了上面介绍的的播放管理功能，可以将特效的渐入/渐出属性绑定到控制视频播放的关键帧通道上，因此不需要再单独手动设置特效的关键帧。

#### 保存预置

特效管理面板提供了一系列按钮用于特效的导入/导出。一个媒体的完整特效链可以作为JSON预置文件被保存到文件中，也可以直接复制到其它的媒体上。

## 参考与致谢

特效节点组的实现参考了以下代码：
- https://github.com/obsproject/obs-studio/blob/master/plugins/obs-filters/data/chroma_key_filter.effect
- https://godotshaders.com/shader/green-screen-chromakey/
- https://www.shadertoy.com/view/7sscD4
- https://www.shadertoy.com/view/4s2GRR

功能演示中使用了以下素材：
- https://pixabay.com/videos/cat-pet-green-screen-green-nature-116648/
- [Big Buck Bunny](https://peach.blender.org/)
