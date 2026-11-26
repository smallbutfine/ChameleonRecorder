# ChameleonRecorder — WLAN Credential Removal & Imager JSON

## Status: DONE (clean image produced; awaiting manual upload + commit decision)

## Goal
Produce a sanitized `ChameleonRecorder.img.xz` with the home-studio WLAN
credentials removed, WITHOUT breaking:
- the `recorder` user (MUST stay passwordless — already working, untouched)
- the fallback hotspot logic (`wifi-fallback.sh` — home-wifi-first, else hotspot)
- NetworkManager connection priorities already set in the image
Plus an `os_list.json` for Raspberry Pi Imager that lets the user type home
WLAN credentials in OS Customisation but does NOT create/overwrite the user.

## What the credentials actually were (corrected finding)
The home SSID is `FRITZ!Box` (UPPERCASE — the hardware DB uses mixed-case
`Fritz!Box`, so a case-sensitive match does NOT touch hardware DBs).
The PSK is a 20-digit number. These were NOT in a single
`preconfigured.nmconnection`. They were scattered as plaintext across BOTH
partitions (live config remnants + free space / deleted-file remnants):
- p1 (FAT32 boot): orphaned `wpa_supplicant.conf` block in free space
  (`ctrl_interface=... ssid="FRITZ!Box" psk="..." key_mgmt=WPA-PSK`).
  The live cloud-init `network-config` had NO WLAN (ethernet only).
- p2 (ext4 rootfs): additional copies in free space / logs.
Total in the full image: `FRITZ!Box` x45, psk x16.

The live `user-data` on the boot partition contains the `recorder` user and a
passwd hash, but NO WLAN. It was left untouched (cloud-init behaviour unchanged
from the original working image).

## Solution (root-free; no loopback mount; sudo needs password)
1. Decompress release `.img.xz` -> `ChameleonRecorder.img` (3.27 GiB).
2. Same-length byte replacement across the WHOLE image (blanks values, keeps
   file structure, corrupts nothing, unrecoverable):
   - `FRITZ!Box`            -> 9 spaces
   - `54898962364446083117` -> 20 spaces
   Implemented in `cr_sanitize.py` (chunked, overlap-safe).
3. Verify: 0 remaining occurrences; identical file size; partition table intact;
   `fsck.fat` clean (dirty bit was pre-existing in the capture); rootfs
   `system-connections` still only `ChameleonHotspot`; `wifi-fallback.sh` intact.
4. `xz -k` -> `ChameleonRecorder.clean.img.xz` (526,912,576 bytes); `xz -t` OK.
5. Copy to `dist/ChameleonRecorder.img.xz` (gitignored) for manual upload.

## os_list.json (no user corruption)
- Raspberry Pi Imager os_list v1 schema; `init_format: cloudinit-rpi`.
- NO username/password/country set here. The Customisation screen still appears;
  the user types ONLY the Wi-Fi SSID/password and MUST leave username,
  password and country BLANK (blank username => imager writes no user block =>
  recorder user not created/overwritten; blank country => DE default kept, safe
  abroad).
- `url` points at the V1.0.0 asset (the file being replaced).
- `extract_size` = 3513623040, `image_download_size` = 526912576.

## Verification checklist (all passed)
- [x] 0 remaining `FRITZ!Box` / psk in clean image
- [x] clean image size == original (3513623040)
- [x] partition table intact (p1 FAT32 512M, p2 ext4 2.8G)
- [x] `fsck.fat` OK (pre-existing dirty bit only)
- [x] rootfs `system-connections` = only ChameleonHotspot
- [x] `wifi-fallback.sh` intact (hotspot logic unchanged)
- [x] `xz -t` passes on recompressed image
- [x] os_list.json valid JSON, correct V1.0.0 URL

## Re-run for future releases
1. Download new release `.img.xz` into WSL `~/cr_work/`.
2. `xz -d` to get `.img`.
3. Edit the two byte strings in `cr_sanitize.py` if the SSID/PSK changed.
4. `python3 cr_sanitize.py` -> `ChameleonRecorder.clean.img`.
5. `xz -k -f ChameleonRecorder.clean.img`; `xz -t` to verify.
6. Update `extract_size` / `image_download_size` / `release_date` / `url` in
   `os_list.json`; copy image to `dist/`; upload both to the release.

## Notes / residual risk (unchanged from original image, NOT introduced here)
- The boot-partition `user-data` still carries a `recorder` passwd hash. This is
  the original image's behaviour; cloud-init only (re)applies it on a new
  instance-id. Blanking WLAN did not alter this. If you want the recorder to be
  provably passwordless even under cloud-init, that is a separate change.


## Addendum: passwordless recorder hardening (cloud-init)
cloud-init is ENABLED (v25.2, NoCloud datasource from /boot/firmware) and the
boot-partition `user-data` carried a `recorder` passwd hash. cloud-init only
re-applies per-instance config when the instance-id is new, so a reflash with a
new instance-id (e.g. imager customisation) could have set that password.
Fix applied to the clean image (cloud-init left ENABLED so imager Wi-Fi works):
- `user-data`: `passwd:` line commented out (`#asswd:`) and hash value blanked;
  `recorder` user block kept with `lock_passwd: false` => no password ever set.
- All 13 copies of the passwd hash across the image blanked (unrecoverable).
- Verified: /etc/shadow recorder field empty; cloud-init 5 services intact;
  WLAN 0; image size unchanged (3513623040); xz -t OK.
New image_download_size = 526913460.
