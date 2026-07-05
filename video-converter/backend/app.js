import express from 'express';
import cors from 'cors';
import multer from 'multer';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import ffmpeg from 'fluent-ffmpeg';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 5000;

// Enable CORS
app.use(cors());

// Create uploads and output directories if they don't exist
const uploadsDir = path.join(__dirname, 'uploads');
const outputDir = path.join(__dirname, 'output');

if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
}

if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadsDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, uniqueSuffix + '-' + file.originalname);
    }
});

const upload = multer({ 
    storage: storage,
    limits: { fileSize: 2 * 1024 * 1024 * 1024 } // 2GB limit
});

// Serve static files from output directory
app.use('/output', express.static(outputDir));

// Upload and convert endpoint
app.post('/api/upload', upload.single('video'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No video file uploaded' });
        }

        const inputPath = req.file.path;
        const videoId = path.basename(req.file.filename, path.extname(req.file.filename));
        const outputPath = path.join(outputDir, videoId);

        // Create output directory for this video
        if (!fs.existsSync(outputPath)) {
            fs.mkdirSync(outputPath, { recursive: true });
        }

        const mpdPath = path.join(outputPath, 'manifest.mpd');

        console.log(`Converting ${inputPath} to DASH format...`);

        // Convert MP4 to DASH format using FFmpeg
        await new Promise((resolve, reject) => {
            ffmpeg(inputPath)
                .outputOptions([
                    '-c:v copy',           // Copy video codec
                    '-c:a copy',           // Copy audio codec
                    '-f dash',             // Output format: DASH
                    '-seg_duration 4',     // Segment duration in seconds
                    '-init_seg_name init_$RepresentationID$.m4s',
                    '-media_seg_name chunk_$RepresentationID$-$Number%05d$.m4s',
                    '-y'                   // Overwrite output files
                ])
                .output(mpdPath)
                .on('start', (cmd) => {
                    console.log('FFmpeg command:', cmd);
                })
                .on('progress', (progress) => {
                    console.log('Progress:', progress.percent ? progress.percent.toFixed(2) + '%' : progress.timemark);
                })
                .on('end', () => {
                    console.log('Conversion completed successfully');
                    resolve(true);
                })
                .on('error', (err) => {
                    console.error('FFmpeg error:', err.message);
                    reject(err);
                })
                .run();
        });

        // Clean up input file
        fs.unlinkSync(inputPath);

        // Return the manifest URL
        const manifestUrl = `http://localhost:${PORT}/output/${videoId}/manifest.mpd`;
        
        res.json({
            success: true,
            message: 'Video converted successfully',
            manifestUrl: manifestUrl,
            videoId: videoId
        });

    } catch (error) {
        console.error('Error processing video:', error);
        res.status(500).json({ 
            error: 'Failed to process video',
            message: error.message 
        });
    }
});

// Get list of converted videos
app.get('/api/videos', (req, res) => {
    try {
        const videos = fs.readdirSync(outputDir)
            .filter(item => fs.statSync(path.join(outputDir, item)).isDirectory())
            .map(videoId => ({
                videoId: videoId,
                manifestUrl: `http://localhost:${PORT}/output/${videoId}/manifest.mpd`
            }));
        
        res.json({ videos });
    } catch (error) {
        res.status(500).json({ error: 'Failed to get video list' });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Uploads directory: ${uploadsDir}`);
    console.log(`Output directory: ${outputDir}`);
});
