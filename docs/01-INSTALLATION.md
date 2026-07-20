# 硬件与安装

## 推荐配置

### RTX 2070 Super 8GB

- 可以完成 RVC 训练、RMVPE 提取、歌曲分离和声音转换。
- 训练建议批量大小 2 至 4。
- YuE 只能考虑量化或显存优化版本，整首生成速度较慢。

### RTX 5060 Ti 16GB

- 更适合本地原创音乐生成与多方案筛选。
- RVC 训练建议批量大小 4 至 8，显存不足时降低。
- MusicGen 中型模型通常需要约 16GB 显存。

## 为什么不把运行环境放进 GitHub

Applio、GPT-SoVITS 和模型权重合计可能超过 10GB。GitHub 仓库只保存工作台代码、配置器和文档，依赖由用户从原作者发布页下载。这可以避免过期二进制、许可证混淆和 Git LFS 成本。

## 安装 Applio

1. 打开 <https://github.com/IAHispano/Applio/releases/latest>。
2. 按发布说明下载 Windows 整合包。
3. 解压到 ASCII 路径，例如 `C:\AI-Singer\Applio`。
4. 不要放入 `Program Files`、OneDrive、中文路径或带空格的目录。
5. 先单独运行一次 Applio，确认显卡识别正常。

## 安装 GPT-SoVITS

1. 打开 <https://github.com/RVC-Boss/GPT-SoVITS/releases/latest>。
2. 根据显卡型号选择普通版或 50 系显卡专用版。
3. 解压到 `C:\AI-Singer\GPT-SoVITS`。
4. 确认目录里存在 `runtime\python.exe` 和 `tools\uvr5`。
5. 在 UVR5 中准备 BS-RoFormer 人声分离权重。

## 配置工作台

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-windows.ps1 `
  -ApplioRoot "C:\AI-Singer\Applio" `
  -GPTSoVITSRoot "C:\AI-Singer\GPT-SoVITS"
```

如果暂时只做原创引导轨换声，可以省略 `GPTSoVITSRoot`。此时训练和“原创歌曲”仍能使用，“AI 翻唱”的自动歌曲分离不可用。

## 验证安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-windows.ps1
```

全部显示通过后，双击 `启动 AI歌手工作台.cmd`。

## 磁盘空间

建议至少保留 50GB。训练切片、中间 WAV、模型检查点和成品不会上传 GitHub，但会保存在 `data` 目录。
