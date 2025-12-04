# 🎭 SpotCue

A live Followspot callsheet tracker for ETC EOS console sessions.

**SpotCue** streamlines followspot operations by synchronizing your cue sheet with your ETC EOS console, providing real-time visual feedback for lighting cues, pickups, and levels.

---

## ✨ Features

- **Real-time Cue Tracking**: Live synchronization with ETC EOS console sessions
- **Visual Feedback**: Color-coded cues (green for fired, red for next/visual cues)
- **Callsheet Management**: Upload and manage CSV-based cue sheets
- **Network Flexible**: Connect to EOS console over network with configurable adapter selection
- **Easy-to-Read Interface**: Clear sections for current cue, next cue, EOS status, and visual cues

---

## 📋 Main GUI Sections

### Current Cue
Displays the latest pinged cue from your call sheet. Pulses green when a spot cue has been fired to grab your attention, also good if you have automated EOS cues!

### Next Cue
Shows the next expected cue from your callsheet in relation to EOS. Glows red when the desk's next cue matches your next spot cue to grab your attention or if you have automated EOS cues!

### EOS
Displays the active and pending ETC EOS cues.

### Visual Cue
If you've labeled a cue as "VISUAL" in your CSV, it appears here and glows red once the last numbered cue before it fires.

**Each section displays:**
- LIVE Status - If you are live in the scene a green tag with "LIVE" will appear.
- DEAD Status - If you are off in the scene a red tag with "RED" will appear.
- LX Cue - A EOS cue number that you have chosen to be cued with.
- Pickup - Your actor's name and action.
- Level - Your noted level number, this influences the appearance of the LIVE/DEAD statis.
- Size - Your noted body size.
- Colour - Your noted  colour.
- Note - Your additional notes.

---

## 🚀 Installation & Usage

### Option 1: Standalone Executable (Recommended for Users)
Simply download and run `SpotCue.exe` — no installation required!

1. Double-click `SpotCue.exe`
2. Configure your network adapter and EOS IP in Settings
3. Upload your CSV callsheet when prompted
4. Start tracking cues!

### Option 2: Python Script (If you would like to have a tinker!)

**Requirements:**
- Python 3.7+
- Required packages: `tkinter`, `pandas`, `socket`, `struct`

**Installation:**
```bash
pip install pandas
python SpotCue.py
```

---

## ⚙️ Settings & Configuration + Help

### Network Setup
1. Open Settings from the main interface in top right corner
2. Select your network adapter
- You must be on the same physical network as your console
- A wired connection is reccomended
- Ensure your IPV4 settings are properly configured so your subnet matches and you are on the same IP range. (e.g. my console is 10.101.90.11, so my machine is 10.101.90.50)
3. Enter your Primary ETC EOS console's IP address
4. The connection status will update when you go back to the main GUI

### CSV Format

Create a spreadsheet with the following column headers (exact capitalization required):

- LX Cue
    - A LX cue number that matches an EOS cue within the current running showfile. Any missed numbers will be presented as soon as possible in the "Current Cue" window, but will not be shown in the "Next Cue" window.
    - Alternativley if you have a visual cue you can put this as "VISUAL", it will then appear in red in the "Upcoming Visual" area when you are a cue before it and will clear away when the GUI moves onto the next cue.
- Pickup
    - This should be just a name with a location/action, there is no "limitation" this is my reccomendation for the best readable result.
- Level
    - This should be a number between 0 and 10, you can add a small note on the end.
    - A level o 0 will make a red tag of "DEAD" appear, anything above this will cause "LIVE" in a green tag to appear. This can help to tell you if you are on in scene with a glance.
- Size
    - This can be for example 1/4, HB, or FB. But you can add a small note on the end.
- Colour
    - This can be anything to best suit your setup. E.g. "L201" or "Light Blue"
- Note
    - Any additional information can be put here. It should be a small notation as word wrapping is not part of this tool to ensure every other section is visable.

**Important:**
- **LX Cue**: Must contain a known LX Cue number or "VISUAL"
- **Level**: If a number is not included a LIVE/DEAD tag will not appear.

### Help

In top right a ? icon is available to view this guide.

---

## 📦 Distribution

This project comes in two formats:

| Format | Use Case | Requirements |
|--------|----------|--------------|
| **SpotCue.exe** | Quick deployment, no setup | Windows only, standalone |
| **SpotCue.py** | Development, customization | Python 3.7+, dependencies |

---

## 🖥️ Created by ChatGPT

I am no coder and so AI has been used to generate the coding for this tool. I am an ETC EOS programmer at heart and an operator on the daily. I have tested this tool with other technicians within shows and we have been enjoying the experience. Myself being neurodivergent an overstimulation of walls of documentation is my biggest enemy and so what sparked this project. I'd still highly reccomend you print physical versions of your callsheets should anything fail or you are absent for a show etc. Paper never grows old.


**Ready to get started?** Download `SpotCue.exe` or run `SpotCue.py` and configure your settings!
