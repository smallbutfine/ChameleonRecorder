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
