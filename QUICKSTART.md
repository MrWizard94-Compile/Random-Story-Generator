# Quick Start Guide

## Before Running the App

1. **Ensure Ollama is installed and running:**
   ```powershell
   ollama serve
   ```
   (Keep this window open while using the app)

2. **Ensure you have at least one model pulled:**
   ```powershell
   ollama pull llama2
   ```

## Starting the GUI

**Option 1: Double-click (Windows)**
- Double-click `run_gui.bat`

**Option 2: Command Line (Windows)**
```powershell
.venv\Scripts\python.exe gui_app.py
```

## First Steps in the App

1. **Check Ollama Status**
   - Look at the status bar (bottom of window)
   - Should show "Ollama: ✓ Connected"

2. **Go to "Model Management" tab**
   - Click "Summon Models" to see available models
   - You should see your pulled models listed

3. **Generate a Story**
   - Go to "Generate" tab
   - Select a model from the dropdown
   - Optionally select genre, tone, and word count
   - Click "Inscribe the Story"
   - Wait for the story to generate (may take a moment)

4. **Save, Copy, or Batch Generate**
   - Save: Click "Save to Archive" to save as markdown
   - Copy: Click "Copy Scroll" to copy to clipboard
   - Batch: Go to "Batch" tab to generate multiple stories

## Tips

- **Larger models produce better stories but take longer:**
  - `llama2` - Good balance of speed and quality
  - `mistral` - Excellent quality, slower
  - `neural-chat` - Fast and decent quality

- **First run takes longer** as the model processes
- **Stories are saved with metadata** (model, genre, tone, timestamp)
- **No internet required** after initial setup

## Troubleshooting

**"Ollama: Not Connected"**
- Make sure the "ollama serve" command is running in another terminal
- Wait a moment and restart the app

**Model not found**
- Try pulling it again: `ollama pull <model_name>`
- Refresh the model list in the app

**Stories taking too long**
- Check if your system is under heavy load
- Try using a smaller model first
- Generator times out after 5 minutes

## Popular Models to Try

- `llama2` - Classic, reliable, good stories
- `mistral` - Excellent quality writing
- `neural-chat` - Fast, conversational
- `starling-lm` - Good for creative writing
- `openchat` - Balanced performance
- `dolphin-mixtral` - Very detailed stories
