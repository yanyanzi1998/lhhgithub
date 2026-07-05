import { useState, useRef, useEffect } from 'react'
import * as dashjs from 'dashjs'
import './App.css'

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [error, setError] = useState<string>('')
  const videoRef = useRef<HTMLVideoElement>(null)
  const playerRef = useRef<any>(null)

  useEffect(() => {
    return () => {
      if (playerRef.current) {
        playerRef.current.reset()
      }
    }
  }, [])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.mp4')) {
        setError('请选择 MP4 格式的视频文件')
        return
      }
      setSelectedFile(file)
      setError('')
      setVideoUrl(null)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('请先选择视频文件')
      return
    }

    setUploading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('video', selectedFile)

      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || '上传失败')
      }

      const data = await response.json()
      setVideoUrl(data.manifestUrl)
    } catch (err: any) {
      setError(err.message || '上传失败')
    } finally {
      setUploading(false)
    }
  }

  useEffect(() => {
    if (videoUrl && videoRef.current) {
      if (playerRef.current) {
        playerRef.current.reset()
      }

      playerRef.current = dashjs.MediaPlayer().create()
      playerRef.current.initialize(videoRef.current, videoUrl, true)
    }
  }, [videoUrl])

  return (
    <div className="app">
      <h1>MP4 to M4S 视频转换器</h1>
      <p className="description">将 MP4 视频转换为 DASH 格式（m4s 片段）并在浏览器中播放</p>

      <div className="upload-section">
        <input
          type="file"
          accept=".mp4"
          onChange={handleFileSelect}
          disabled={uploading}
          id="file-input"
        />
        <label htmlFor="file-input" className="file-label">
          {selectedFile ? selectedFile.name : '选择 MP4 视频文件'}
        </label>
        
        {selectedFile && !videoUrl && (
          <button 
            onClick={handleUpload} 
            disabled={uploading}
            className="upload-btn"
          >
            {uploading ? '上传并转换中...' : '上传并转换视频'}
          </button>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      {videoUrl && (
        <div className="player-section">
          <h2>播放转换后的视频</h2>
          <video 
            ref={videoRef} 
            controls 
            className="video-player"
          />
          <p className="success-message">✓ 转换成功！视频已通过 dash.js 播放</p>
        </div>
      )}

      <div className="info-section">
        <h3>技术说明</h3>
        <ul>
          <li>后端：Node.js + Express + Fluent-FFmpeg</li>
          <li>前端：React + TypeScript + Vite</li>
          <li>视频处理：FFmpeg</li>
          <li>播放器：Dash.js</li>
          <li>输出格式：DASH (.mpd + .m4s 片段)</li>
        </ul>
      </div>
    </div>
  )
}

export default App
