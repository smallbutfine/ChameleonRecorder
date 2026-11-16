# --- /usr/local/bin/wifi-fallback.sh ---
#!/bin/bash
sleep 25
if ! ip -4 addr show wlan0 | grep -q "inet "; then
    COUNTRY=$(iw reg get | awk "/country/ {print substr(\$2,1,2); exit}")
    [ -z "$COUNTRY" ] || [ "$COUNTRY" = "00" ] && iw reg set DE
    nmcli device disconnect wlan0 2>/dev/null
    sleep 2
    nmcli connection delete ChameleonHotspot 2>/dev/null
    nmcli device wifi hotspot ifname wlan0 con-name ChameleonHotspot band bg channel 6 ssid "ChameleonRecorder" password "chameleon123"
fi

# --- /etc/systemd/system/wifi-fallback.service ---
[Unit]
Description=Fallback Wi-Fi Hotspot for ChameleonRecorder
After=NetworkManager.service
Wants=NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/wifi-fallback.sh

[Install]
WantedBy=multi-user.target
