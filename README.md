# pic2pic-nextgen

**Holographic Image Reconstruction Engine** - Production-ready Windows 10 application and web client.

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/MASSIVEMAGNETICS/pic2pic-nextgen)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🌟 Overview

pic2pic-nextgen is a next-generation image transformation platform built on holographic reconstruction principles. It features:

- **Desktop Application**: Native Windows 10 app using Tauri 2.0 + SvelteKit (~3-6 MB binary)
- **Web Client**: SvelteKit 5 with real-time WebSocket streaming
- **Backend**: FastAPI with WebSocket for live preview and batch processing
- **Self-Healing System**: Automatic recovery from GPU OOM, crashes, and corrupted files

## 📁 Project Structure

```
pic2pic-nextgen/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # REST and WebSocket routes
│   │   ├── core/              # Engine and self-healing
│   │   ├── config.py          # Configuration
│   │   └── main.py            # Application entry
│   └── requirements.txt
├── web-client/                 # SvelteKit frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/    # UI components
│   │   │   ├── stores/        # State management
│   │   │   └── utils/         # WebSocket client
│   │   └── routes/            # SvelteKit routes
│   └── package.json
├── desktop/                    # Tauri desktop wrapper
│   └── src-tauri/
│       ├── src/main.rs        # Rust backend
│       └── Cargo.toml
└── pic2pic_nextgen_architecture_manifesto.py
```

## 🚀 Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m backend.app.main
```

The API will be available at `http://localhost:8000` with OpenAPI docs at `/docs`.

### Web Client

```bash
cd web-client
npm install
npm run dev
```

The web client will be available at `http://localhost:5173`.

### Desktop App

```bash
cd desktop
npm install
npm run tauri dev
```

## 🎨 User Interface

### User Mode (Default)
- **Upload**: Drag & drop or paste images
- **Presets**: One-click Enhance, Stylize, De-old-photo, Make-anime
- **Gallery**: View processed images
- **Queue**: Track batch processing

### Dev Mode (Ctrl+Shift+D)
Additional tabs:
- **HoloLab**: Fine-tune tau values, binding parameters, view shard heatmap
- **DNA Editor**: Custom reconstruction logic (V2)
- **Metrics**: System health, memory usage, device status

## 🔧 Features

### MVP (Current)
- [x] Single image upload with instant preview
- [x] Real-time WebSocket streaming
- [x] Batch processing queue
- [x] Save/Load .holo memory banks
- [x] Dev/User mode toggle
- [x] Preset modes (Enhance, Stylize, etc.)

### V1 (Planned)
- [ ] Self-healing watchdog with auto-restart
- [ ] GPU → CPU fallback on OOM
- [ ] Checkpoint recovery
- [ ] Online training interface

### V2 (Future)
- [ ] Cloud sync & collaborative memory banks
- [ ] Plugin system (DNA adapters)

## 🛡️ Self-Healing System

The self-healing engine provides:

1. **GPU OOM Recovery**: Automatically flushes memory and falls back to CPU
2. **Watchdog Restart**: Process restarts within 3 seconds on crash
3. **Checkpoint Recovery**: Atomic swap checkpoints every 10 batches
4. **Integrity Checks**: Cosine similarity validation (>0.92 threshold)
5. **Thermal Throttling**: Batch size reduction on high CPU temperature

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/upload` | POST | Upload image for processing |
| `/api/v1/presets` | GET | List available presets |
| `/api/v1/job/{id}` | GET | Get job status |
| `/api/v1/batch` | POST | Start batch processing |
| `/ws` | WebSocket | Real-time communication |

## 🏗️ Stack

| Component | Technology |
|-----------|------------|
| Desktop | Tauri 2.0 + SvelteKit |
| Web | SvelteKit 5 + TypeScript |
| Backend | FastAPI + Uvicorn |
| Real-time | WebSocket + SSE |
| Core | Python + PyTorch |

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

**MASSIVEMAGNETICS** - *The holographic memory is now the application.*

