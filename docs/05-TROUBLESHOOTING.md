# 常见问题与排错

## 双击启动没有反应

运行 `scripts\verify-windows.ps1`。重点检查 `config.json`、Applio Python 和端口 9875。

## 页面打不开

- 等待 10 至 30 秒再访问 <http://127.0.0.1:9875/>。
- 查看 `runtime-logs\workbench-error.log`。
- 端口被占用时，在 `config.json` 中更换端口。

## 模型列表为空

- 训练是否真正完成。
- `data\models\模型名` 是否同时包含 `.pth` 和 `.index`。
- 点击“刷新模型列表”。

## CUDA 显存不足

- 将训练批量大小降低到 2 或 1。
- 关闭 Stable Diffusion、游戏和其他占用显卡的软件。
- 缩短一次处理的歌曲。
- 不要同时运行 YuE 与 RVC 训练。

## 无法分离歌曲

- 检查 GPT-SoVITS 路径。
- 检查 `tools\uvr5\uvr5_weights` 下是否存在配置的 BS-RoFormer 权重。
- 使用 WAV、MP3、FLAC 或 M4A 输入。

## 输出仍像原歌手

- 检查是否选择了正确模型。
- 增加干净清唱数据并重新训练。
- 确认 FAISS `.index` 与 `.pth` 来自同一个模型。

## 输出破音或机器人感

- 调整升降调，让源音域接近模型音域。
- 关闭过强的音准修正。
- 使用更干净的人声引导轨。
- 增加目标声音高音、低音和长音录音。

## 中文路径问题

第三方音频和 FAISS 组件在 Windows 上可能无法处理中文或特殊字符。建议整个安装路径使用英文字母，例如 `C:\AI-Singer`。
