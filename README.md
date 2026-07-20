# AI Singer Workbench

从个人声音训练、AI 翻唱，到原创 AI 歌曲制作的一站式本地工作流。

这个项目面向没有编程经验的 Windows 用户。它把多个成熟开源项目串成一条清晰的制作链：

```text
个人干声录音 -> RVC 音色模型
现有歌曲 -> 人声/伴奏分离 -> 音色替换 -> 混音导出
原创词曲 -> 虚拟歌手引导轨 -> 个人音色替换 -> 原创伴奏 -> 混音导出
```

> 本仓库不包含任何第三方模型、商业歌曲或训练声音。大型运行环境需要从原项目下载。

## 能做什么

- 上传多段个人录音，训练自己的 RVC 歌声音色模型。
- 上传一首歌曲，自动分离原唱与伴奏，再将原唱替换成你的声音。
- 上传原创引导人声和原创伴奏，直接制作成你的 AI 原唱。
- 调整升降调、人声音量和轻度音准修正。
- 导出无损 WAV 与 320 kbps MP3。
- 所有声音处理都可以在本机完成。

## 先理解三个概念

1. **音色模型**负责让输出听起来像你，不负责写旋律。
2. **演唱引导轨**提供音准、节奏、咬字、颤音和情绪。
3. **伴奏**负责乐器、和声与歌曲结构。

因此，原创 AI 歌曲不是让 RVC 凭空唱歌，而是先产生一条专业的原创引导人声，再换成你的音色。

## 所用开源项目

| 环节 | 项目 | 用途 | 是否必需 |
|---|---|---|---|
| 声音训练与转换 | [IAHispano/Applio](https://github.com/IAHispano/Applio) | RVC 训练、RMVPE 音高提取、声音转换 | 必需 |
| 人声与伴奏分离 | [RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) | 使用 UVR5 / BS-RoFormer 分离歌曲 | 翻唱需要 |
| 可控原创演唱 | [openutau/OpenUtau](https://github.com/openutau/OpenUtau) | 编辑 MIDI、歌词、颤音和表情 | 原创推荐 |
| 高质量歌声合成 | [openvpi/DiffSinger](https://github.com/openvpi/DiffSinger) | 产生可控的虚拟歌手引导轨 | 原创可选 |
| 文本生成完整歌曲 | [multimodal-art-projection/YuE](https://github.com/multimodal-art-projection/YuE) | 从歌词生成主唱与伴奏 | 原创可选 |
| 伴奏草图 | [facebookresearch/audiocraft](https://github.com/facebookresearch/audiocraft) | MusicGen 文本/旋律生成音乐 | 原创可选 |

各项目拥有自己的许可证与模型条款，详见 [第三方项目说明](docs/THIRD_PARTY.md)。

## 硬件要求

| 硬件 | 最低 | 推荐 |
|---|---:|---:|
| 系统 | Windows 10 64 位 | Windows 11 64 位 |
| NVIDIA 显卡 | 8 GB 显存 | 16 GB 以上显存 |
| 内存 | 16 GB | 32 GB |
| 剩余磁盘 | 25 GB | 50 GB 以上 |

- 8 GB 显存适合 RVC 训练、翻唱和 OpenUtau。
- 16 GB 显存更适合本地 MusicGen、YuE 量化版本和批量处理。
- 没有 NVIDIA 显卡仍可使用部分功能，但速度会明显下降。

## Windows 快速开始

### 第一步：准备依赖

1. 下载 [Applio 最新 Windows 版](https://github.com/IAHispano/Applio/releases/latest)。
2. 需要自动分离歌曲时，下载 [GPT-SoVITS 最新 Windows 版](https://github.com/RVC-Boss/GPT-SoVITS/releases/latest)。
3. 将两个程序放在没有空格和特殊符号的目录，例如：

```text
C:\AI-Singer\Applio
C:\AI-Singer\GPT-SoVITS
```

### 第二步：配置工作台

右键 PowerShell 打开本项目目录，运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-windows.ps1 `
  -ApplioRoot "C:\AI-Singer\Applio" `
  -GPTSoVITSRoot "C:\AI-Singer\GPT-SoVITS"
```

脚本会检查显卡、Python、Applio、GPT-SoVITS、FFmpeg 与分离模型，并生成本机专用的 `config.json`。

### 第三步：启动

双击：

```text
启动 AI歌手工作台.cmd
```

浏览器会打开：<http://127.0.0.1:9875/>

## 第一次训练自己的声音

1. 准备 20 至 30 分钟干净录音，朗读与清唱都要有。
2. 不要添加伴奏、混响、变声、美化或自动修音。
3. 打开“训练我的声音”，一次上传所有录音。
4. 模型名称使用英文，例如 `my_voice`。
5. RTX 2070 Super 可先使用 300 轮、批量大小 4。
6. 训练完成后，模型与索引会出现在 `data/models/my_voice`。

完整录音方法见 [录音与数据集指南](docs/02-RECORDING.md)。

## 制作 AI 翻唱

1. 打开“AI 翻唱”。
2. 上传你有权处理的歌曲。
3. 选择个人声音模型。
4. 根据原唱音域调整升降调。
5. 点击“开始制作”。

工作台依次执行：歌曲分离、声音转换、伴奏混合、WAV/MP3 导出。

## 制作原创 AI 歌曲

### 路线 A：可控精品路线

1. 写歌词并确定 BPM、调性、段落结构。
2. 在 OpenUtau 或 DiffSinger 中输入歌词与 MIDI 旋律。
3. 调整音准、时值、颤音、力度、气口与咬字。
4. 导出“干声引导轨”，不要混入伴奏和混响。
5. 在 DAW 或其他工具中制作原创伴奏。
6. 打开工作台的“原创歌曲”，分别上传引导人声与伴奏。
7. 换成自己的声音并导出。

### 路线 B：快速生成路线

1. 使用 YuE 输入原创歌词、曲风和结构，生成歌曲草案。
2. 将草案送入“AI 翻唱”流程，自动分离主唱与伴奏。
3. 将主唱替换为你的声音。
4. 筛选多个版本，再进行人工修词、修旋律和混音。

更详细的工作流见 [原创音乐指南](docs/04-ORIGINAL-MUSIC.md)。

## 目录结构

```text
AI-Singer-Workbench/
├─ workbench/              工作台程序
├─ scripts/                Windows 配置、启动与检查脚本
├─ docs/                   中文教程与故障排查
├─ data/                   运行后生成，不上传 GitHub
│  ├─ recordings/          个人录音副本
│  ├─ songs/               导入的歌曲
│  ├─ separated/           人声与伴奏
│  ├─ models/              个人模型和索引
│  ├─ outputs/             WAV 与 MP3 成品
│  └─ logs/                每个处理阶段的日志
└─ config.json             本机路径配置，不上传 GitHub
```

## 已知边界

- 强混响、现场录音、多人和声可能无法彻底分离。
- 原唱音域与目标声音差距过大时可能产生电子感或破音。
- RVC 保留引导轨的唱法，但不会自动创造新的旋律与歌词。
- 100 首 AI 翻唱适合测试曲风，不建议再次作为训练数据，否则会累积分离与转换瑕疵。

## 合法与负责任使用

- 只训练你本人或已明确授权的声音。
- 发布翻唱前确认词曲、录音制品和伴奏的授权范围。
- 原创发布时保存歌词、MIDI、工程文件、提示词和模型来源记录。
- 不要冒充他人、制造误导性录音或绕过平台标识规则。

## 文档

- [硬件和安装](docs/01-INSTALLATION.md)
- [录音与数据集](docs/02-RECORDING.md)
- [训练与 AI 翻唱](docs/03-TRAINING-AND-COVERS.md)
- [原创音乐完整流程](docs/04-ORIGINAL-MUSIC.md)
- [常见问题与排错](docs/05-TROUBLESHOOTING.md)
- [第三方项目和许可证](docs/THIRD_PARTY.md)

## 许可证

本仓库自行编写的代码和文档使用 [MIT License](LICENSE)。第三方程序、模型和数据不属于本许可证范围。
