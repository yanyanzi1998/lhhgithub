#!/usr/bin/env python3
"""
MP4 to DASH Converter with Local Player
Converts MP4 videos to fragmented MP4 (fMP4) format for DASH streaming playback.
"""

import os
import sys
import subprocess
import json
import threading
import http.server
import socketserver
import webbrowser
import argparse
from pathlib import Path


class DASHConverter:
    """Handles conversion of MP4 to DASH-compatible fragmented MP4 format."""
    
    def __init__(self, packager_path="/usr/local/bin/packager"):
        self.packager_path = packager_path
        
    def verify_packager(self):
        """Verify that shaka-packager is available."""
        try:
            result = subprocess.run(
                [self.packager_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Using shaka-packager: {result.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Error accessing packager: {e}")
            return False
        except FileNotFoundError:
            print(f"✗ Packager not found at {self.packager_path}")
            return False
    
    def convert(self, input_file, output_dir, segment_duration=4, verbose=False):
        """
        Convert MP4 to DASH format with fragmented MP4 segments.
        
        Args:
            input_file: Path to input MP4 file
            output_dir: Directory for output files
            segment_duration: Duration of each segment in seconds
            verbose: Enable verbose output
            
        Returns:
            dict: Conversion results including manifest path and status
        """
        input_path = Path(input_file).resolve()
        output_path = Path(output_dir).resolve()
        
        if not input_path.exists():
            return {"success": False, "error": f"Input file not found: {input_path}"}
        
        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate output filenames based on input
        base_name = input_path.stem
        
        # Output paths - use $Number$ (subprocess handles escaping)
        video_segment_template = str(output_path / f"{base_name}_video_$Number$.m4s")
        audio_segment_template = str(output_path / f"{base_name}_audio_$Number$.m4s")
        init_video = str(output_path / f"{base_name}_video_init.mp4")
        init_audio = str(output_path / f"{base_name}_audio_init.mp4")
        manifest_path = output_path / f"{base_name}.mpd"
        
        # Build packager command for DASH with fragmented MP4
        cmd = [
            self.packager_path,
            f"input={input_path},stream=video,segment_template={video_segment_template},"
            f"init_segment={init_video}",
            f"input={input_path},stream=audio,segment_template={audio_segment_template},"
            f"init_segment={init_audio}",
            "--segment_duration", str(segment_duration),
            "--mpd_output", str(manifest_path),
        ]
        
        # Add extra flags for better compatibility
        cmd.extend([
            "--generate_static_mpd",
        ])
        
        if verbose:
            print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                return {"success": False, "error": f"Packager failed: {error_msg}"}
            
            # Verify output files were created
            if not manifest_path.exists():
                return {"success": False, "error": "Manifest file was not created"}
            
            # List generated files
            generated_files = list(output_path.glob("*"))
            
            return {
                "success": True,
                "manifest_path": str(manifest_path),
                "output_directory": str(output_path),
                "generated_files": [str(f) for f in generated_files],
                "base_url": None  # Will be set by server
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Conversion timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class DASHHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for serving DASH content with correct MIME types."""
    
    mime_types = {
        '.mpd': 'application/dash+xml',
        '.m4s': 'video/iso.segment',
        '.mp4': 'video/mp4',
        '.m3u8': 'application/vnd.apple.mpegurl',
        '.ts': 'video/MP2T',
    }
    
    def guess_type(self, path):
        """Return the correct MIME type for DASH files."""
        ext = Path(path).suffix.lower()
        return self.mime_types.get(ext, super().guess_type(path))
    
    def end_headers(self):
        """Add CORS headers for local development."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


def create_player_html(mpd_filename, port):
    """Create an HTML file with a DASH player."""
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DASH Video Player</title>
    <script src="https://cdn.dashjs.org/latest/dash.all.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #fff;
        }}
        
        .container {{
            max-width: 1200px;
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            font-size: 2em;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            text-align: center;
            color: #a0a0a0;
            margin-bottom: 30px;
        }}
        
        .video-wrapper {{
            position: relative;
            width: 100%;
            padding-top: 56.25%; /* 16:9 Aspect Ratio */
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }}
        
        .video-wrapper video {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
        
        .info-panel {{
            margin-top: 25px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
        }}
        
        .info-panel h3 {{
            margin-bottom: 15px;
            color: #00d4ff;
        }}
        
        .file-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        
        .info-item {{
            background: rgba(255, 255, 255, 0.05);
            padding: 12px;
            border-radius: 8px;
        }}
        
        .info-item label {{
            display: block;
            font-size: 0.85em;
            color: #a0a0a0;
            margin-bottom: 5px;
        }}
        
        .info-item span {{
            font-size: 1.1em;
            word-break: break-all;
        }}
        
        .controls {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        
        button {{
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
        }}
        
        .btn-primary {{
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
        }}
        
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        
        .status {{
            margin-top: 15px;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .status.playing {{
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 DASH Video Player</h1>
        <p class="subtitle">Fragmented MP4 (fMP4) Streaming</p>
        
        <div class="video-wrapper">
            <video 
                id="videoPlayer" 
                controls 
                autoplay
                data-dashjs-player
            >
                <source src="{mpd_filename}" type="application/dash+xml">
                Your browser does not support DASH playback.
            </video>
        </div>
        
        <div class="info-panel">
            <h3>📊 Stream Information</h3>
            <div class="file-info">
                <div class="info-item">
                    <label>Manifest URL</label>
                    <span>{mpd_filename}</span>
                </div>
                <div class="info-item">
                    <label>Format</label>
                    <span>DASH (fMP4)</span>
                </div>
                <div class="info-item">
                    <label>Player</label>
                    <span>dash.js</span>
                </div>
                <div class="info-item">
                    <label>Server</label>
                    <span>http://localhost:{port}</span>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn-primary" onclick="togglePlay()">⏯️ Play/Pause</button>
            <button class="btn-secondary" onclick="toggleFullscreen()">⛶ Fullscreen</button>
            <button class="btn-secondary" onclick="reloadPlayer()">🔄 Reload</button>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
    </div>
    
    <script>
        const video = document.getElementById('videoPlayer');
        const statusDiv = document.getElementById('status');
        
        function showStatus(message, type) {{
            statusDiv.textContent = message;
            statusDiv.className = 'status ' + type;
            statusDiv.style.display = 'block';
            setTimeout(() => {{
                statusDiv.style.display = 'none';
            }}, 3000);
        }}
        
        function togglePlay() {{
            if (video.paused) {{
                video.play();
                showStatus('Playing', 'playing');
            }} else {{
                video.pause();
                showStatus('Paused', '');
            }}
        }}
        
        function toggleFullscreen() {{
            if (document.fullscreenElement) {{
                document.exitFullscreen();
            }} else {{
                document.querySelector('.video-wrapper').requestFullscreen();
            }}
        }}
        
        function reloadPlayer() {{
            video.load();
            showStatus('Reloading...', 'playing');
        }}
        
        // Event listeners
        video.addEventListener('play', () => showStatus('Playing', 'playing'));
        video.addEventListener('pause', () => showStatus('Paused', ''));
        video.addEventListener('waiting', () => showStatus('Buffering...', 'playing'));
        video.addEventListener('playing', () => showStatus('Playing', 'playing'));
        video.addEventListener('error', (e) => showStatus('Playback error', ''));
        
        // Initialize dash.js player
        document.addEventListener('DOMContentLoaded', function() {{
            const player = dashjs.MediaPlayer().create();
            player.initialize(video, '{mpd_filename}', true);
            
            // Enable debugging
            player.updateSettings({{
                'debug': {{
                    'logLevel': dashjs.Debug.LOG_LEVEL_WARNING
                }},
                'streaming': {{
                    'buffer': {{
                        'stableBufferTime': 30,
                        'bufferTimeDefault': 30
                    }}
                }}
            }});
            
            console.log('DASH Player initialized');
        }});
    </script>
</body>
</html>
'''
    return html_content


def start_server(directory, port=8080):
    """Start HTTP server for serving DASH content."""
    
    os.chdir(directory)
    
    handler = DASHHTTPHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🌐 Server running at http://localhost:{port}")
        print(f"📁 Serving files from: {directory}")
        print("Press Ctrl+C to stop the server")
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(
        description="Convert MP4 to DASH format and play locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp4                     Convert and start server on default port
  %(prog)s input.mp4 -o ./output         Specify output directory
  %(prog)s input.mp4 -p 9000             Use custom port
  %(prog)s input.mp4 --serve-only        Only serve existing DASH files
        """
    )
    
    parser.add_argument("input", nargs="?", help="Input MP4 file path")
    parser.add_argument("-o", "--output", default="./dash_output", 
                       help="Output directory for DASH files (default: ./dash_output)")
    parser.add_argument("-p", "--port", type=int, default=8080,
                       help="HTTP server port (default: 8080)")
    parser.add_argument("-s", "--segment-duration", type=int, default=4,
                       help="Segment duration in seconds (default: 4)")
    parser.add_argument("--serve-only", action="store_true",
                       help="Only start server without conversion")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--no-browser", action="store_true",
                       help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 MP4 to DASH Converter & Player")
    print("=" * 60)
    
    converter = DASHConverter()
    
    # Verify packager is available
    if not converter.verify_packager():
        print("\nPlease install shaka-packager:")
        print("  wget https://github.com/shaka-project/shaka-packager/releases/download/v3.8.0/packager-linux-x64 -O packager")
        print("  chmod +x packager && sudo mv packager /usr/local/bin/")
        sys.exit(1)
    
    if args.serve_only:
        # Just serve existing files
        output_dir = Path(args.output).resolve()
        if not output_dir.exists():
            print(f"✗ Output directory not found: {output_dir}")
            sys.exit(1)
        
        mpd_files = list(output_dir.glob("*.mpd"))
        if not mpd_files:
            print(f"✗ No .mpd files found in {output_dir}")
            sys.exit(1)
        
        print(f"\n✓ Found {len(mpd_files)} manifest file(s)")
        manifest_path = mpd_files[0]
        print(f"  Using: {manifest_path.name}")
        
    elif args.input:
        # Convert MP4 to DASH
        print(f"\n📥 Input: {args.input}")
        print(f"📤 Output: {args.output}")
        print(f"⏱️  Segment Duration: {args.segment_duration}s")
        
        result = converter.convert(
            args.input,
            args.output,
            args.segment_duration,
            args.verbose
        )
        
        if not result["success"]:
            print(f"\n✗ Conversion failed: {result['error']}")
            sys.exit(1)
        
        print(f"\n✓ Conversion successful!")
        print(f"  Manifest: {result['manifest_path']}")
        print(f"  Files generated: {len(result['generated_files'])}")
        
        manifest_path = Path(result['manifest_path'])
        
    else:
        parser.print_help()
        sys.exit(1)
    
    # Create player HTML
    output_dir = Path(args.output).resolve()
    player_html = output_dir / "player.html"
    
    mpd_relative = f"./{manifest_path.name}"
    html_content = create_player_html(mpd_relative, args.port)
    
    with open(player_html, 'w') as f:
        f.write(html_content)
    
    print(f"\n✓ Player page created: {player_html}")
    
    # Start server in a separate thread
    server_thread = threading.Thread(
        target=start_server,
        kwargs={"directory": str(output_dir), "port": args.port},
        daemon=True
    )
    server_thread.start()
    
    # Give server time to start
    import time
    time.sleep(1)
    
    # Open browser
    if not args.no_browser:
        player_url = f"http://localhost:{args.port}/player.html"
        print(f"\n🌐 Opening player at: {player_url}")
        try:
            webbrowser.open(player_url)
        except Exception as e:
            print(f"Note: Could not open browser automatically: {e}")
            print(f"Please open: {player_url}")
    
    print("\n" + "=" * 60)
    print("Server is running. Press Ctrl+C to exit.")
    print("=" * 60)
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
