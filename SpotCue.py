import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import pandas as pd
import socket
import struct
import time
import subprocess

EPS = 1e-3
EOS_PORT = 3032  # ETC EOS OSC over TCP default


HELP_TEXT = r"""
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
"""


# =====================================================================
# CSV Parsing
# =====================================================================
def read_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    if "LX Cue" not in df.columns:
        raise KeyError("CSV must contain 'LX Cue'")
    df["LX Cue (num)"] = pd.to_numeric(df["LX Cue"], errors="coerce")
    return df.reset_index(drop=True)


def format_row(row: pd.Series) -> str:
    lines = []
    for col in row.index:
        if col.lower() == "lx cue (num)":
            continue
        val = row[col]
        if pd.isna(val) or val == "":
            if col.lower() in ("colour", "color"):
                val = "NONE"
            else:
                val = ""
        lines.append(f"{col}: {val}")
    return "\n".join(lines)


# =====================================================================
# Adapter listing (Windows)
# =====================================================================
def list_adapters():
    adapters = []
    try:
        output = subprocess.check_output("ipconfig", shell=True, text=True)
    except Exception:
        return [("Unknown — 0.0.0.0 / Unknown", "0.0.0.0", "Unknown")]

    name = ip = mask = None

    for line in output.splitlines():
        s = line.strip()

        if s.endswith(":") and "adapter" in s.lower():
            if name and ip:
                adapters.append((f"{name} — {ip} / {mask}", ip, mask))
            name = s[:-1]
            ip = mask = None
            continue

        if "IPv4" in s:
            parts = s.split(":")
            if len(parts) > 1:
                ip = parts[1].strip()
        if "Subnet Mask" in s:
            parts = s.split(":")
            if len(parts) > 1:
                mask = parts[1].strip()

    if name and ip:
        adapters.append((f"{name} — {ip} / {mask}", ip, mask))

    return adapters or [("Unknown — 0.0.0.0 / Unknown", "0.0.0.0", "Unknown")]


# =====================================================================
# TCP OSC Helpers
# =====================================================================
def recv_exact(sock: socket.socket, size: int) -> bytes | None:
    buf = b""
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def read_packet(sock: socket.socket) -> bytes | None:
    header = recv_exact(sock, 4)
    if not header:
        return None
    (size,) = struct.unpack(">I", header)
    return recv_exact(sock, size)


def parse_osc_string(data: bytes, offset: int) -> tuple[str, int]:
    end = data.find(b"\0", offset)
    if end == -1:
        return "", offset
    s = data[offset:end].decode(errors="ignore")
    pad = (4 - (end + 1) % 4) % 4
    return s, end + 1 + pad


# =====================================================================
# Main Application
# =====================================================================
class SpotCueApp:
    def __init__(self):
        # Data
        self.df: pd.DataFrame | None = None
        self.current_cue: float | None = None
        self.current_lx: float | None = None
        self.next_lx: float | None = None
        self.pending_cue: float | None = None

        # Network
        self.eos_ip = "10.101.90.11"
        self.adapters = list_adapters()
        self.adapter_ip = self.adapters[0][1]

        # TCP control
        self.tcp_stop = threading.Event()
        self.tcp_thread: threading.Thread | None = None

        # TK window
        self.root = tk.Tk()
        self.root.title("SpotCue")
        self.root.configure(bg="black")
        self.root.geometry("1280x720")
        self.root.iconbitmap("spotcue.ico")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Settings window handle
        self.settings_window: tk.Toplevel | None = None
        self.settings_status_label: tk.Label | None = None
        self.adapter_info: tk.Label | None = None

        # Pulse state
        self._pulse_active = False
        self._last_current_text = None

        # Build UI
        self.build_ui()

        # Must load CSV at startup
        self.prompt_csv_if_missing()

        # Start TCP thread
        self.start_tcp_client()

    # -----------------------------------------------------------------
    # Build UI
    # -----------------------------------------------------------------
    def build_ui(self):
        # Title
        title = tk.Label(
            self.root, text="SpotCue",
            font=("Arial", 32, "bold"),
            fg="white", bg="black"
        )
        title.pack(pady=5)

        # Top buttons
        topbar = tk.Frame(self.root, bg="black")
        topbar.pack(fill="x")

        tk.Button(topbar, text="[?]", fg="white", bg="#222222",
                  command=self.open_help).pack(side="right", padx=6, pady=6)
        tk.Button(topbar, text="[⚙]", fg="white", bg="#222222",
                  command=self.open_settings).pack(side="right", padx=6, pady=6)

        # Main grid
        grid = tk.Frame(self.root, bg="black")
        grid.pack(fill="both", expand=True)

        for r in range(2):
            grid.rowconfigure(r, weight=1)
        for c in range(2):
            grid.columnconfigure(c, weight=1)

        self.grid = grid

        # CURRENT -------------------------------------------------------
        self.frame_current = tk.Frame(
            grid, bg="black",
            highlightthickness=10,
            highlightbackground="black", highlightcolor="black"
        )
        self.frame_current._orig_color = "black"
        self.frame_current.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        hdr = tk.Frame(self.frame_current, bg="black")
        hdr.pack(anchor="nw", fill="x")
        tk.Label(hdr, text="Current Cue", fg="white", bg="black",
                 font=("Arial", 24)).pack(side="left")
        self.current_status = self._make_status(hdr)

        self.current_text = tk.Label(
            self.frame_current, text="Waiting…",
            fg="white", bg="black",
            font=("Arial", 24), anchor="nw", justify="left"
        )
        self.current_text.pack(fill="both", expand=True, padx=10, pady=10)

        # NEXT ----------------------------------------------------------
        self.frame_next = tk.Frame(
            grid, bg="black",
            highlightthickness=10,
            highlightbackground="black", highlightcolor="black"
        )
        self.frame_next.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        hdr = tk.Frame(self.frame_next, bg="black")
        hdr.pack(anchor="nw", fill="x")
        tk.Label(hdr, text="Next Cue", fg="white", bg="black",
                 font=("Arial", 24)).pack(side="left")
        self.next_status = self._make_status(hdr)

        self.next_text = tk.Label(
            self.frame_next, text="N/A",
            fg="grey", bg="black",
            font=("Arial", 24), anchor="nw", justify="left"
        )
        self.next_text.pack(fill="both", expand=True, padx=10, pady=10)

        # EOS -----------------------------------------------------------
        self.frame_eos = tk.Frame(grid, bg="black")
        self.frame_eos.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        tk.Label(self.frame_eos, text="EOS", fg="orange", bg="black",
                 font=("Arial", 24)).pack(anchor="nw")

        self.eos_active_label = tk.Label(
            self.frame_eos, text="Active: —",
            fg="orange", bg="black", anchor="w", font=("Arial", 40)
        )
        self.eos_active_label.pack(fill="x", padx=10, pady=(10, 5))

        self.eos_pending_label = tk.Label(
            self.frame_eos, text="Pending: —",
            fg="orange", bg="black", anchor="w", font=("Arial", 24)
        )
        self.eos_pending_label.pack(fill="x", padx=10)

        # VISUAL --------------------------------------------------------
        self.frame_visual = tk.Frame(
            grid, bg="black",
            highlightthickness=10,
            highlightbackground="black", highlightcolor="black"
        )
        self.frame_visual.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        hdr = tk.Frame(self.frame_visual, bg="black")
        hdr.pack(anchor="nw", fill="x")
        tk.Label(hdr, text="Upcoming Visual", fg="white", bg="black",
                 font=("Arial", 24)).pack(side="left")
        self.visual_status = self._make_status(hdr)

        self.visual_text = tk.Label(
            self.frame_visual, text="",
            fg="darkgrey", bg="black",
            font=("Arial", 24), anchor="nw", justify="left"
        )
        self.visual_text.pack(fill="both", expand=True, padx=10, pady=10)

    # -----------------------------------------------------------------
    def _make_status(self, parent):
        lbl = tk.Label(
            parent, text="", fg="white", bg="black",
            font=("Arial", 16, "bold"), bd=0, highlightthickness=0
        )
        lbl._protected_bg = "black"
        lbl._protected_fg = "white"
        lbl.pack(side="left", padx=10)
        return lbl

    # -----------------------------------------------------------------
    # CSV Prompt
    # -----------------------------------------------------------------
    def prompt_csv_if_missing(self):
        if self.df is not None and not self.df.empty:
            return
        messagebox.showinfo("CSV Required", "Please load your CSV.")
        self.upload_csv()
        if self.df is None or self.df.empty:
            messagebox.showerror("No CSV", "Cannot run without CSV.")
            self.root.destroy()

    # -----------------------------------------------------------------
    # Settings Window
    # -----------------------------------------------------------------
    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("520x340")
        win.configure(bg="black")
        self.settings_window = win

        frame = tk.Frame(win, bg="black")
        frame.pack(fill="x", padx=12, pady=10)

        # Adapter
        tk.Label(frame, text="Local Adapter:", fg="cyan",
                 bg="black", font=("Arial", 12, "bold")).grid(row=0, column=0)

        names = [n for n, _, _ in self.adapters]
        current = names[0]
        for n, ip, _ in self.adapters:
            if ip == self.adapter_ip:
                current = n

        self.adapter_var = tk.StringVar(value=current)
        opt = tk.OptionMenu(frame, self.adapter_var, *names,
                            command=self._choose_adapter)
        opt.config(bg="#222222", fg="white")
        opt.grid(row=0, column=1)

        # Adapter info
        info = "0.0.0.0 / Unknown"
        for n, ip, mask in self.adapters:
            if n == current:
                info = f"{ip} / {mask}"
        tk.Label(frame, text="Selected:", fg="white", bg="black")\
            .grid(row=1, column=0)
        self.adapter_info = tk.Label(frame, text=info, fg="white", bg="black")
        self.adapter_info.grid(row=1, column=1)

        # EOS IP
        tk.Label(frame, text="EOS IP:", fg="cyan",
                 bg="black", font=("Arial", 12, "bold")).grid(row=2, column=0, pady=10)

        self.eos_ip_var = tk.StringVar(value=self.eos_ip)
        ip_entry = tk.Entry(frame, textvariable=self.eos_ip_var,
                            justify="center", width=15)
        ip_entry.grid(row=2, column=1)
        ip_entry.bind("<Return>", lambda e: self._update_eos_ip())
        ip_entry.bind("<FocusOut>", lambda e: self._update_eos_ip())

        # Connection status
        self.settings_status_label = tk.Label(
            frame, text="Status: UNKNOWN", fg="orange", bg="black",
            font=("Arial", 14)
        )
        self.settings_status_label.grid(row=3, column=0, columnspan=2, pady=10)

        # Bottom
        bottom = tk.Frame(win, bg="black")
        bottom.pack(fill="x", padx=12, pady=10)

        tk.Button(bottom, text="Upload CSV", bg="#222222", fg="white",
                  command=self.upload_csv).pack(side="left")

        win.protocol("WM_DELETE_WINDOW", win.destroy)

    def _choose_adapter(self, name):
        for n, ip, mask in self.adapters:
            if n == name:
                self.adapter_ip = ip
                self.adapter_info.config(text=f"{ip} / {mask}")
                self.start_tcp_client()

    def _update_eos_ip(self):
        ip = self.eos_ip_var.get().strip()
        if ip:
            self.eos_ip = ip
            self.start_tcp_client()

    # -----------------------------------------------------------------
    def open_help(self):
        win = tk.Toplevel(self.root)
        win.title("Help")
        win.geometry("800x600")
        win.configure(bg="black")

        text = tk.Text(win, wrap="word", fg="white",
                       bg="black", font=("Consolas", 12))
        text.insert("1.0", HELP_TEXT)
        text.config(state="disabled")

        sb = ttk.Scrollbar(win, command=text.yview)
        text["yscrollcommand"] = sb.set

        sb.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)

    # -----------------------------------------------------------------
    # TCP OSC
    # -----------------------------------------------------------------
    def start_tcp_client(self):
        self.tcp_stop.set()
        self.tcp_stop = threading.Event()
        t = threading.Thread(target=self._tcp_loop, daemon=True)
        self.tcp_thread = t
        t.start()

    def _update_settings_status(self, text):
        if self.settings_status_label and \
           self.settings_window and self.settings_window.winfo_exists():
            self.settings_status_label.config(text=f"Status: {text}")

    def _tcp_loop(self):
        while not self.tcp_stop.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)

                # Bind to selected adapter
                try:
                    if self.adapter_ip and self.adapter_ip != "0.0.0.0":
                        sock.bind((self.adapter_ip, 0))
                except Exception:
                    pass

                sock.connect((self.eos_ip, EOS_PORT))
                self._update_settings_status("CONNECTED")
                sock.settimeout(None)

                while not self.tcp_stop.is_set():
                    packet = read_packet(sock)
                    if not packet:
                        break

                    addr, _ = parse_osc_string(packet, 0)
                    parts = addr.split("/")

                    if len(parts) >= 7 and parts[1] == "eos" \
                       and parts[2] == "out" and parts[4] == "cue":
                        section = parts[3]
                        cu = parts[6]
                        try:
                            cue = float(cu)
                        except:
                            continue

                        if section == "active":
                            self.root.after(0, lambda c=cue: self._handle_active(c))
                        elif section == "pending":
                            self.root.after(0, lambda c=cue: self._handle_pending(c))

                sock.close()

            except Exception:
                self._update_settings_status("RECONNECTING…")
                time.sleep(2)

        self._update_settings_status("DISCONNECTED")

    # -----------------------------------------------------------------
    # Active / Pending
    # -----------------------------------------------------------------
    def _handle_active(self, cue):
        self.current_cue = cue
        self.eos_active_label.config(text=f"Active: {cue}")
        self.update_display_for_eos(cue)

    def _handle_pending(self, cue):
        self.pending_cue = cue
        self.eos_pending_label.config(text=f"Pending: {cue}")
        if self.current_cue is not None:
            self.update_display_for_eos(self.current_cue)

    # -----------------------------------------------------------------
    # NO-BOUNCE PULSE (colour only)
    # -----------------------------------------------------------------
    def pulse(self):
        if self._pulse_active:
            return

        self._pulse_active = True

        # Save original colour
        try:
            orig_color = self.frame_current.cget("highlightbackground")
        except:
            orig_color = "black"

        steps = 12
        interval_ms = 25

        def step(i):
            if i > steps * 2:
                # Restore
                self.frame_current.config(
                    highlightbackground=orig_color,
                    highlightcolor=orig_color
                )
                self._pulse_active = False
                return

            # Triangle wave 0→1→0
            if i <= steps:
                t = i / steps
            else:
                t = (2 * steps - i) / steps

            # Green fade 30% → 100% → 30%
            g = int(255 * (0.3 + 0.7 * t))
            g = max(0, min(255, g))
            col = f"#00{g:02x}00"

            # Colour only — NO thickness change → NO movement
            self.frame_current.config(
                highlightbackground=col,
                highlightcolor=col
            )

            self.root.after(interval_ms, lambda: step(i + 1))

        step(0)

    # -----------------------------------------------------------------
    # Background colouring
    # -----------------------------------------------------------------
    def set_frame_bg(self, frame, color):
        def apply(w):
            if hasattr(w, "_protected_bg"):
                w.config(
                    bg=w._protected_bg,
                    fg=w._protected_fg,
                    bd=0, highlightthickness=0
                )
                return

            try:
                w.config(bg=color)
                if color.lower() in ("#550000", "#8b0000"):
                    w.config(fg="white")
            except:
                pass

            for c in w.winfo_children():
                apply(c)

        apply(frame)

    # -----------------------------------------------------------------
    # Display update
    # -----------------------------------------------------------------
    def update_display_for_eos(self, eos_cue):
        if self.df is None or self.df.empty:
            return

        df = self.df
        numeric = df[df["LX Cue (num)"].notna()]
        if numeric.empty:
            return

        first_lx = numeric.iloc[0]["LX Cue (num)"]

        # BEFORE FIRST CUE -------------------------------------------------
        if eos_cue < first_lx:
            txt = "Waiting for first cue…"
            self.current_text.config(text=txt)
            self._update_status(self.current_status, None)
            self._last_current_text = txt

            first_row = numeric.iloc[0]
            self.next_lx = first_row["LX Cue (num)"]
            self.next_text.config(text=format_row(first_row))
            self._update_status(self.next_status, first_row.get("Level"))

            self.update_visual_for_lx(first_lx)

            if self.pending_cue and abs(self.pending_cue - first_lx) < EPS:
                self.set_frame_bg(self.frame_next, "#550000")
            else:
                self.set_frame_bg(self.frame_next, "black")

            return

        # NORMAL MAPPING --------------------------------------------------
        exact = numeric[abs(numeric["LX Cue (num)"] - eos_cue) < EPS]
        if not exact.empty:
            idx = exact.index[0]
        else:
            idx = numeric[numeric["LX Cue (num)"] <= eos_cue].index[-1]

        row = df.loc[idx]
        lx = row["LX Cue (num)"]
        self.current_lx = lx

        # Current — pulse on change
        new_text = format_row(row)
        if self._last_current_text != new_text:
            self.pulse()

        self.current_text.config(text=new_text)
        self._last_current_text = new_text
        self._update_status(self.current_status, row.get("Level"))

        # Next
        nxt = numeric[numeric.index > idx]
        if not nxt.empty:
            next_row = nxt.iloc[0]
            self.next_lx = next_row["LX Cue (num)"]
            self.next_text.config(text=format_row(next_row))
            self._update_status(self.next_status, next_row.get("Level"))
        else:
            self.next_lx = None
            self.next_text.config(text="End of cues")
            self._update_status(self.next_status, None)

        # Pending highlight
        if self.pending_cue and self.next_lx:
            pending_match = numeric[
                abs(numeric["LX Cue (num)"] - self.pending_cue) < EPS
            ]
            if not pending_match.empty and \
               pending_match.iloc[0]["LX Cue (num)"] == self.next_lx:
                self.set_frame_bg(self.frame_next, "#550000")
            else:
                self.set_frame_bg(self.frame_next, "black")
        else:
            self.set_frame_bg(self.frame_next, "black")

        # Visual
        self.update_visual_for_lx(lx)

    # -----------------------------------------------------------------
    # Status label (LIVE/DEAD)
    # -----------------------------------------------------------------
    def _update_status(self, label, level):
        try:
            lvl = float(level)
        except:
            label.config(
                text="", bg="black", fg="white",
                bd=0, highlightthickness=0
            )
            label._protected_bg = "black"
            label._protected_fg = "white"
            return

        if lvl > 0:
            label.config(
                text="LIVE", bg="green", fg="black",
                bd=0, highlightthickness=0
            )
            label._protected_bg = "green"
            label._protected_fg = "black"
        else:
            label.config(
                text="DEAD", bg="red", fg="white",
                bd=0, highlightthickness=0
            )
            label._protected_bg = "red"
            label._protected_fg = "white"

    # -----------------------------------------------------------------
    # Visual logic
    # -----------------------------------------------------------------
    def update_visual_for_lx(self, current_lx):
        if self.df is None or self.df.empty or current_lx is None:
            self.visual_text.config(text="")
            self._update_status(self.visual_status, None)
            self.set_frame_bg(self.frame_visual, "black")
            return

        df = self.df
        numeric = df[df["LX Cue (num)"].notna()]
        visual = df[df["LX Cue"].astype(str).str.lower() == "visual"]

        for i, row in visual.iterrows():
            prev = numeric[numeric.index < i]
            if prev.empty:
                continue
            trigger = prev.iloc[-1]["LX Cue (num)"]

            if abs(trigger - current_lx) < EPS:
                self.visual_text.config(text=format_row(row))
                self._update_status(self.visual_status, row.get("Level"))
                self.set_frame_bg(self.frame_visual, "#8B0000")
                return

        self.visual_text.config(text="")
        self._update_status(self.visual_status, None)
        self.set_frame_bg(self.frame_visual, "black")

    # -----------------------------------------------------------------
    # CSV Loading
    # -----------------------------------------------------------------
    def upload_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            self.df = read_csv(path)
            messagebox.showinfo("CSV", "Loaded successfully.")
        except Exception as e:
            messagebox.showerror("CSV Error", str(e))

    # -----------------------------------------------------------------
    def on_close(self):
        self.tcp_stop.set()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# =====================================================================
# Entry
# =====================================================================
if __name__ == "__main__":
    SpotCueApp().run()
