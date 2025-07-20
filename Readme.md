# 📘 Proslic SI3228 Userspace Driver (Experimental)

This project is a **userspace software** implementation that attempts to initialize and operate the **Silicon Labs SI3228** – a 2-channel FXS chip.  

The work is based on reversing SPI bus captures from a **Zyxel EX5601** router running its original firmware. While functional in some areas, the implementation is **experimental** and relies on several kernel and device tree patches to properly interface with the hardware.  

---

## ⚙️ Overview

This software communicates with the SI3228 via SPI through a kernel module (`/dev/proslic`) and provides basic initialization and playback functionality.  

### 🔨 Current implementation:
- Reverse-engineered SPI sequences from Zyxel EX5601 proprietary firmware.  
- Userspace driver written in Python (`main.py`).  
- Kernel patches required for:
  - Proper SPI device registration.
  - Character device (`/dev/proslic`) for userspace ↔ kernel communication.
  - ALSA sound card and codec integration (needed to provide active **BCLK** on the I²S bus).  

> ⚠️ Note: At present, the SPI device is **not registered as an ALSA codec**. Kernel-side patches will be released later as the implementation stabilizes.

---

## 📋 Requirements

### 🖥 Hardware
- Zyxel EX5601 running **OpenWrt (stable)**.
- 
### 🛠 Software
- Custom kernel patches for:
  - SPI device definition.
  - ALSA sound card and codec.
- Python 3 environment with:
  - `python-uci`
  - `python-gpiod`

---

## 🚀 How to Test (EX5601 with OpenWrt)

1. **Apply the kernel patches** (for SPI and ALSA integration).
2. **Install required Python packages:**
   ```bash
   opkg install python3 pyuci python3-gpiod
   ```

3. Enable BCLK on the I²S bus by starting sound playback:
    ```bash
    amixer sset 'O018 I150_Switch' on
    amixer sset 'O019 I151_Switch' on
    amixer sset 'O124 I032_Switch' on
    amixer sset 'O125 I033_Switch' on
    aplay -D hw:0,0 -f S16_LE -c 2 -r 16000 /dev/urandom
    ```

4. Copy the driver files to a directory and start it on a new terminal:
    ```bash
    python main.py
    ```
5. Observe: A simple initialization sequence should start. When lifting the handset, you should hear noise.

6. Play a test sound: (Stop the previous random playback first)
    ```bash
    aplay -D hw:0,0 -f S16_LE -c 1 -r 16000 testfile.wav
    ```

    The audio should play through the handset.

## ✅ What Works (So Far)
 - 🔊 Sound playback (channel 0)
 - 🎙 Sound recording (untested)
 - ☎️ Ring generation (Work In Progress)
 - 📞 Hook detection (Work In Progress)
 - 🅰 Channel 0 functional (See above)
 - 🅱 Channel 1 partially functional (WIP)

## ⚠️ Shortcomings / Known Issues
 - ❌ No DTMF detection (Asterisk cannot detect tones from the PCM stream).
 - ❌ Tone generator not fully reverse-engineered → cannot generate arbitrary signals yet.
 - ❌ Many registers and functionalities still unknown or handled by the proprietary firmware.
 - 🌍 Current implementation replicates settings captured for ETSI (EU market).
 - 🕹 Must manually play sound to enable BCLK (otherwise the chip won’t respond).
 - ⚠️ Only a single channel reliably operational.

## 📢 Notes

This project is still highly experimental. Kernel patches and further refinements will be published as the driver matures.
Expect bugs, missing features, and the need for manual intervention during testing.