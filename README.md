# ChameleonRecorder OS (Raspberry Pi 4B – 64-bit)

**ChameleonRecorder** is a headless, plug-and-play multitrack WAV recorder OS image for the **Raspberry Pi 4 Model B (64-bit)**. It automatically detects any class-compliant USB audio interface or digital mixing console, records uncompressed 24-bit multitrack WAV files directly to a USB flash drive, and provides a mobile-friendly web remote control with live level meters—including an automatic fallback Wi-Fi hotspot for stage and rehearsal use.

---

## Key Features

* **Universal USB Audio Support:** Automatically detects single or multiple class-compliant USB audio interfaces (e.g., Behringer UMC1820, UMC204HD, XR18, X32, MOTU AVB, Focusrite, RME, Zoom) at **48 kHz** (with automatic **44.1 kHz** fallback).
* **Multi-Device & Automatic ADAT Clock Sync:**
  * Supports recording multiple USB audio interfaces simultaneously (`jackd` + `alsa_in`), prioritizing the interface with the highest channel count as primary device.
  * Automatically detects valid ADAT clock signals (`Optical In ADAT/SMUX Validity`) on Behringer UMC1820 interfaces and switches them to external ADAT clock sync.
* **Web Remote Control (`ChameleonRecorder`):**
  * Accessible from any phone, tablet, or laptop browser on port **`:8080`**.
  * **Per-Device & Per-Channel Arming:** Enable/disable individual interfaces or specific input channels to reduce file sizes without unplugging cables.
  * **Live Peak Level Meters:** Real-time dBFS meters for every capture channel.
  * **File Management:** Start/Stop recording, delete the last take, delete individual files, download individual WAVs, or download all recordings bundled as a timestamped `.zip` archive.
* **Automatic Fallback Wi-Fi Hotspot:**
  * Connects to your configured home/studio Wi-Fi if available.
  * If no known Wi-Fi network is found within 25 seconds after boot, it automatically creates its own Wi-Fi access point (**SSID:** `ChameleonRecorder`, **Password:** `chameleon123`) with the web interface at **`http://10.42.0.1:8080`**.
* **Physical Hardware Controls (Optional):** Supports optional pushbuttons and status LED on the Raspberry Pi GPIO header.

---

## Quick Start & Installation

### 1. Flash the Image via Raspberry Pi Imager
1. Download the latest **`daw-image.img.xz`** from the [Releases](../../releases) page (or use the custom repository URL in Raspberry Pi Imager).
2. Open **Raspberry Pi Imager**, select **Raspberry Pi 4**, choose the downloaded `.img.xz` file, and write it to a microSD card (16 GB or larger).
3. *(Optional)* In Raspberry Pi Imager's **OS Customisation** settings, you can pre-configure your studio Wi-Fi network and Wi-Fi country code. If you skip this step, the Pi will automatically boot into standalone hotspot mode.

### 2. Connect Storage & Audio Hardware
1. **USB Storage:** Plug a USB flash drive or SSD formatted as **`exFAT`** or **`ext4`** (recommended to avoid the 4 GB file size limit of FAT32) into one of the **blue USB 3.0 ports**. It mounts automatically at `/media/usb0`.
2. **USB Audio Interface(s):** Connect your USB audio interface or digital mixer to the Raspberry Pi and power it on.

### 3. Open the Web Remote
* **Via Fallback Hotspot (No Router Needed):**
  1. Connect your phone or laptop to the Wi-Fi network **`ChameleonRecorder`** (Password: **`chameleon123`**).
  2. Open **`http://10.42.0.1:8080`** in your browser.
* **Via Home / Studio Wi-Fi:**
  1. Find the Pi's IP address on your router (or use `http://DAW.local:8080`).
  2. Open **`http://<PI_IP_ADDRESS>:8080`** in your browser.

---

## Optional Hardware Buttons & Status LED (GPIO)

If you want physical tactile controls in addition to the web remote, connect momentary pushbuttons and an LED to the Raspberry Pi 40-pin GPIO header (BCM numbering):

| Component | GPIO Pin (BCM) | Physical Header Pin | Function |
| :--- | :--- | :--- | :--- |
| **Record / Stop Button** | `GPIO 3` | Pin 5 (to GND Pin 6) | Toggles recording Start / Stop |
| **Delete Last Button** | `GPIO 4` | Pin 7 (to GND Pin 9) | Deletes the most recent `.wav` file |
| **Both Buttons Held** | `GPIO 3 + 4` | Pin 5 + Pin 7 | Safely shuts down the Raspberry Pi |
| **Status LED (+ Resistor)** | `GPIO 18` | Pin 12 (to GND Pin 14) | **Solid ON:** Audio interface ready<br>**Blinking (1s):** Recording in progress<br>**3 Quick Blinks:** Last take deleted |

---

## Multi-Interface & Word Clock / ADAT Sync Guide

* **Mixed USB Interfaces (e.g., UMC1820 + UMC204HD):** Connect both via USB. `ChameleonRecorder` automatically assigns the interface with the most channels as the `jackd` master and binds additional interfaces via `alsa_in` with adaptive drift compensation.
* **Sample-Accurate 36-Channel Setup (2× UMC1820 + 2× ADA8200):**
  1. Set **ADA8200 #1** to **`MASTER 48 kHz`** and connect its `WORD CLOCK OUT` (75Ω BNC) to **ADA8200 #2** (`SLAVE WC IN`).
  2. Connect `ADAT OUT` of ADA8200 #1 → `ADAT IN` of **UMC1820 #1**, and `ADAT OUT` of ADA8200 #2 → `ADAT IN` of **UMC1820 #2**.
  3. Set the front-panel `OPT I/O` button on both UMC1820 units to **ADAT**.
  4. On boot (or when pressing **Re-Scan USB Audio Device**), the Pi automatically detects the valid ADAT signal on both UMC1820 units and switches both to external ADAT clock sync.

---

## SSH Access & Default Credentials

* **Username:** `recorder`
* **Hostname:** `DAW` (`DAW.local`)
* **Web Remote Port:** `8080`
* **Scripts Directory:** `/home/recorder/bin/` (`startcapiture`, `start_jack`, `rec`, `del_last`, `web_remote.py`, `jack_meter.py`, `hotkeys`, `steady`, `blink`)

---

## Acknowledgments

Built on Raspberry Pi OS (64-bit) using `jackd2`, `jack_capture`, and inspired by [danielappelt/caPiture](https://github.com).


## OS Image Release & Installation (Raspberry Pi Imager)

A ready-to-flash 64-bit OS image (`daw-image.img.xz`) is coming soon to the **[Releases](../../releases)** section of this repository. You do not need to manually install Linux packages or configure audio servers—simply flash the image and boot your Raspberry Pi 4B.

### How to Flash the Image with Raspberry Pi Imager

1. **Download the Image:** Download the latest `daw-image.img.xz` file from the **[Releases](../../releases)** page once published. *(You do not need to extract the `.xz` archive—Raspberry Pi Imager handles it directly.)*
2. **Open Raspberry Pi Imager:** Download and launch the official [Raspberry Pi Imager](https://raspberrypi.com) on your Windows, macOS, or Linux computer.
3. **Choose Device:** Click **Choose Device** and select **Raspberry Pi 4**.
4. **Choose Operating System:** Click **Choose OS**, scroll down to the bottom of the list, select **Use custom**, and pick the downloaded `daw-image.img.xz` file.
5. **Choose Storage:** Insert your microSD card (16 GB or larger) and select it under **Choose Storage**.
6. **Optional OS Customisation:**
   * Click **Next** and choose **Edit Settings** if you want to pre-configure your home/studio Wi-Fi credentials, set your Wi-Fi country code, or add an SSH password/key for the `recorder` user.
   * If you skip OS Customisation (click **No**), the Pi will automatically start its standalone **`ChameleonRecorder`** Wi-Fi hotspot (`10.42.0.1`) on first boot.
7. **Write the Image:** Click **Yes** to confirm and wait for Raspberry Pi Imager to finish writing and verifying the SD card.
8. **Boot & Record:** Insert the microSD card into your Raspberry Pi 4B, connect your USB flash drive and USB audio interface(s), and power it on.
