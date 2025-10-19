# Raspberry Pi Chat Display Setup

These notes capture the full process for preparing a Raspberry Pi Zero W (v1.1) with the Waveshare 7" DSI LCD (product 12885) to run this chat display in console mode.

## 1. Flash and Boot Raspberry Pi OS
- Download the 32-bit Raspberry Pi OS Lite (Bookworm) image.
- Flash the image onto a microSD card.
- Before first boot, configure 2.4 GHz Wi-Fi credentials so the Pi can connect on startup (e.g., using `raspi-config` or a preseeded `wpa_supplicant.conf`). Note the deployment network uses the `Rasp-123` SSID.

## 2. Enable the Waveshare LCD
Follow the vendor guide: <https://www.waveshare.com/wiki/7inch_LCD_for_Pi#Introducing_the_Raspberry_Pi_OS_fork>

1. Download the overlay package: <https://files.waveshare.com/wiki/7inch-DSI-LCD-(with-cam)/7DPI-DTBO.zip>
2. Extract and copy the two `.dtbo` files into `/boot/overlays/` on the Pi.
3. Edit `/boot/firmware/config.txt` (requires `sudo`):

   ```ini
   dtoverlay=vc4-kms-v3d
   dtoverlay=vc4-kms-DPI-7inch
   dtoverlay=waveshare-7dpi
   dtparam=rotate=90
   ```

4. Reboot the Pi to apply the overlay changes: `sudo reboot`

## 3. Stay in Console Mode
- Disable the desktop auto-login so the Pi boots to a text console:
  - `sudo raspi-config`
  - System Options → Boot / Auto Login → **Console (Text console, requiring login)**
- Reboot when prompted.

## 4. Install Chat Dependencies
```bash
sudo apt update
sudo apt install python3 python3-venv python3-flask python3-requests git
```

Clone or update this repository and install Python requirements as needed:
```bash
git pull
```

## 5. Improve Console Legibility
Set a larger console font so the LCD text is readable:

```bash
sudo dpkg-reconfigure console-setup
```

- Keyboard layout → **UTF-8**
- Character set → **Guess optimal**
- Font → **Terminus**
- Font size → **10x20**

## 6. Launch the Chat
- Export your Groq API keys as documented in `config.py` or populate them in a `.env` file.
- Start the control panel to supervise the chat loop:

  ```bash
  python3 control_panel.py
  ```

## 7. Enable Auto-Start (systemd)
To have the control panel launch whenever the Raspberry Pi boots, install the systemd unit provided in `systemd/chatbot-control-panel.service`.

1. Edit the unit file so `WorkingDirectory`, `EnvironmentFile`, `ExecStart`, and `User` match your setup (the committed version assumes the repo lives at `/home/rasp/chat_bot` and runs as the `rasp` user—adjust if yours differs).
2. Copy the unit into place and reload systemd:
   ```bash
   sudo cp systemd/chatbot-control-panel.service /etc/systemd/system/chatbot-control-panel.service
   sudo systemctl daemon-reload
   ```
3. Enable the service so it starts on boot, then start it immediately:
   ```bash
   sudo systemctl enable chatbot-control-panel.service
   sudo systemctl start chatbot-control-panel.service
   ```
4. Check the status or logs if you need to troubleshoot (use `-f` to follow logs live):
   ```bash
   sudo systemctl status chatbot-control-panel.service
   sudo journalctl -u chatbot-control-panel.service
   sudo journalctl -u chatbot-control-panel.service -f
   ```
5. Make sure the `.env` file referenced by `EnvironmentFile=` exists (even an empty file is fine) so the service can load its environment variables.

## Local Development Notes
Create and activate a virtual environment, then install the Flask and Requests dependencies before running the control panel locally:

```bash
cd ~/chat_bot
python3 -m venv .venv
source .venv/bin/activate
pip install flask requests
python3 control_panel.py
```
