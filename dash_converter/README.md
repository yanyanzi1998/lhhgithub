# MP4 to DASH Converter & Player

一个本地软件，用于将 MP4 视频转换为 DASH 格式（fragmented MP4）并使用 dash.js 播放器进行播放。

## 功能特点

- ✅ 将 MP4 视频转换为 DASH 流媒体格式
- ✅ 生成 fragmented MP4 (fMP4) 分段文件
- ✅ 内置 HTTP 服务器，支持正确的 MIME 类型
- ✅ 美观的 Web 播放器界面（基于 dash.js）
- ✅ 自动打开浏览器播放
- ✅ 支持自定义分段时长、输出目录和端口

## 系统要求

- Python 3.6+
- shaka-packager（已预装）
- 现代浏览器（Chrome、Firefox、Edge 等）

## 安装

shaka-packager 已经安装在系统中。如果需要手动安装：

```bash
wget https://github.com/shaka-project/shaka-packager/releases/download/v3.8.0/packager-linux-x64 -O packager
chmod +x packager
sudo mv packager /usr/local/bin/
```

## 使用方法

### 基本用法

```bash
python3 dash_converter.py input.mp4
```

这将：
1. 转换 `input.mp4` 为 DASH 格式
2. 在 `./dash_output` 目录生成输出文件
3. 启动 HTTP 服务器（默认端口 8080）
4. 自动打开浏览器播放视频

### 命令行选项

```
usage: dash_converter.py [-h] [-o OUTPUT] [-p PORT] [-s SEGMENT_DURATION]
                         [--serve-only] [-v] [--no-browser]
                         [input]

 positional arguments:
  input                 Input MP4 file path

 optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory for DASH files (default: ./dash_output)
  -p PORT, --port PORT  HTTP server port (default: 8080)
  -s SEGMENT_DURATION, --segment-duration SEGMENT_DURATION
                        Segment duration in seconds (default: 4)
  --serve-only          Only start server without conversion
  -v, --verbose         Enable verbose output
  --no-browser          Don't open browser automatically
```

### 示例

```bash
# 转换并播放，使用默认设置
python3 dash_converter.py video.mp4

# 指定输出目录
python3 dash_converter.py video.mp4 -o ./my_output

# 使用自定义端口
python3 dash_converter.py video.mp4 -p 9000

# 设置分段时长为 6 秒
python3 dash_converter.py video.mp4 -s 6

# 只启动服务器（不转换），用于播放已转换的文件
python3 dash_converter.py --serve-only -o ./existing_output

# 不自动打开浏览器
python3 dash_converter.py video.mp4 --no-browser
```

## 输出文件

转换后会生成以下文件：

- `{name}.mpd` - DASH  manifest 文件
- `{name}_video_init.mp4` - 视频初始化分段
- `{name}_audio_init.mp4` - 音频初始化分段
- `{name}_video_1.m4s`, `{name}_video_2.m4s`, ... - 视频分段
- `{name}_audio_1.m4s`, `{name}_audio_2.m4s`, ... - 音频分段
- `player.html` - 内置播放器页面

## 技术说明

### DASH 格式

DASH (Dynamic Adaptive Streaming over HTTP) 是一种自适应比特率流媒体技术。本工具生成的是 **fragmented MP4 (fMP4)** 格式的 DASH 流，具有以下优势：

- 更好的浏览器兼容性
- 更高效的传输
- 支持自适应码率切换

### 播放器

使用 [dash.js](https://github.com/Dash-Industry-Forum/dash.js) 参考播放器，这是一个开源的 JavaScript DASH 播放器库。

## 故障排除

### 无法找到 packager

确保 shaka-packager 已正确安装：

```bash
packager --version
```

### 视频无法播放

1. 检查浏览器控制台是否有错误
2. 确保 HTTP 服务器正在运行
3. 确认 `.mpd` 文件的 MIME 类型为 `application/dash+xml`

### 没有声音

某些视频可能只有视频轨道或音频轨道。转换器会自动检测并处理可用的轨道。

## 许可证

MIT License
