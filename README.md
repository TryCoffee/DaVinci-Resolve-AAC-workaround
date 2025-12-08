# DaVinci Resolve AAC Workaround 🎬

A **PyQt5 desktop utility** created as a **workaround for DaVinci Resolve’s limited AAC audio support on Linux**.
The app batch-converts audio streams in `.mp4` and `.mkv` files to **FLAC**, allowing smooth imports into **DaVinci Resolve Studio** without audio issues.

This tool exists because sometimes software just refuses to cooperate.

---

## ✨ Why This Exists

DaVinci Resolve on Linux:
- ❌ Fails to import AAC audio correctly

**Solution:** Convert AAC → FLAC while keeping video untouched.

---

## 🔥 Features

- Batch convert `.mp4` / `.mkv` files
- Audio converted to **FLAC (lossless)**
- Video stream copied (no re-encode, no quality loss)
- Clean dark-themed GUI
- Progress bar
- Ability to stop conversion
- Persistent settings (remembers last folders)
- Full FFmpeg logs with copy-to-clipboard support

---


## 📷 User Interface

- File list with sizes
- Dedicated FFmpeg log viewer
- Minimal, no-bullshit controls

---

## ✅ Supported Formats

### Input
- `.mp4`
- `.mkv`

### Output
- Same container as input
- Audio → **FLAC**
- Video → untouched

FFmpeg command used internally:

```bash
ffmpeg -i input.mkv -c:v copy -c:a flac -y converted_input.mkv
```

## 📦 Requirements

### System
- Linux (tested on Fedora / KDE / Wayland)
- FFmpeg available in `PATH`

### Python Dependencies
```bash
pip install PyQt5
```
Or install it with your system package manager.

## 🚀 Usage

Clone repo wherever you want. I keep it in ~/Apps folder
```bash
git clone https://github.com/TryCoffee/DaVinci-Resolve-AAC-workaround.git ~/Apps/draw
cd ~/Apps/draw
```
Run the python program
```bash
python3 ~/Apps/draw/main.py
```
You can also create a desktop entry which is included in repo
```bash
sudo cp ~/Apps/draw/DRAW.desktop ~/usr/share/applications
