# MP4 to M4S 视频转换器

一个基于 Node.js 后端和 React + TypeScript + Vite 前端的视频转换应用，使用 FFmpeg 将 MP4 视频转换为 DASH 格式（m4s 片段），并通过 dash.js 在浏览器中播放。

## 技术栈

- **后端**: Node.js + Express + Multer + Fluent-FFmpeg
- **前端**: React + TypeScript + Vite
- **视频处理**: FFmpeg
- **播放器**: Dash.js
- **输出格式**: DASH (.mpd manifest + .m4s 片段)

## 项目结构

```
video-converter/
├── backend/
│   ├── app.js              # Express 后端主程序
│   └── package.json        # Node.js 依赖
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # React 主组件
│   │   ├── App.css         # 样式文件
│   │   └── index.css       # 全局样式
│   ├── package.json
│   └── vite.config.ts      # Vite 配置
└── README.md
```

## 安装与运行

### 1. 安装后端依赖

```bash
cd backend
npm install
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动后端服务

```bash
cd backend
npm start
```

后端服务将在 http://localhost:5000 运行

### 4. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

前端服务将在 http://localhost:3000 运行

### 5. 生产构建

```bash
cd frontend
npm run build
```

构建后的文件将输出到 `frontend/dist` 目录

## 使用方法

1. 打开浏览器访问 http://localhost:3000
2. 点击"选择 MP4 视频文件"按钮上传视频
3. 上传后会自动开始转换为 DASH 格式
4. 转换完成后，视频将自动在页面中播放

## 功能特性

- ✓ 支持 MP4 格式视频上传
- ✓ 使用 FFmpeg 转换为 DASH 格式
- ✓ 生成 .mpd manifest 文件和 .m4s 视频片段
- ✓ 使用 dash.js 在浏览器中播放
- ✓ 美观的用户界面
- ✓ 实时状态反馈

## API 接口

### POST /api/upload
上传视频文件并转换为 DASH 格式
- 参数：`video` (FormData)
- 返回：`{ success, message, manifestUrl, videoId }`

### GET /api/videos
获取已转换的视频列表
- 返回：`{ videos: [{ videoId, manifestUrl }] }`

### GET /output/:videoId/manifest.mpd
获取 DASH manifest 文件

### GET /output/:videoId/*.m4s
获取 DASH 视频片段

## 注意事项

- 需要安装 FFmpeg
- 视频转换可能需要较长时间，取决于视频大小
- 建议使用 Chrome、Firefox 等现代浏览器
