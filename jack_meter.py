#!/usr/bin/env python3
import os
if os.path.exists("/home/recorder/bin/setsession"):
    for line in open("/home/recorder/bin/setsession"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            os.environ[k] = v.strip("\"'")

import ctypes, math, time, json, sys

try:
    libjack = ctypes.CDLL("libjack.so.0")
except OSError:
    print("{}")
    sys.exit(0)

libjack.jack_client_open.restype = ctypes.c_void_p
libjack.jack_get_ports.restype = ctypes.POINTER(ctypes.c_char_p)
libjack.jack_port_register.restype = ctypes.c_void_p
libjack.jack_port_name.restype = ctypes.c_char_p
libjack.jack_port_get_buffer.restype = ctypes.POINTER(ctypes.c_float)

status = ctypes.c_int()
client = libjack.jack_client_open(b"chameleon_meter", 1, ctypes.byref(status))
if not client:
    print("{}")
    sys.exit(0)

ports_ptr = libjack.jack_get_ports(ctypes.c_void_p(client), None, b"32 bit float mono audio", 2)
src_ports, in_ports, peaks = [], [], {}

i = 0
while ports_ptr and ports_ptr[i]:
    pname = ports_ptr[i].decode()
    if not pname.startswith("chameleon_meter:"):
        in_p = libjack.jack_port_register(ctypes.c_void_p(client), f"in_{i}".encode(), b"32 bit float mono audio", 1, 0)
        if in_p:
            src_ports.append(pname)
            in_ports.append(in_p)
            peaks[pname] = 0.0
    i += 1

PROCESS_CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_uint32, ctypes.c_void_p)
def process(nframes, arg):
    for idx, pname in enumerate(src_ports):
        buf = libjack.jack_port_get_buffer(ctypes.c_void_p(in_ports[idx]), nframes)
        if buf:
            m = 0.0
            for s in range(0, nframes, 4):
                v = abs(buf[s])
                if v > m: m = v
            if m > peaks[pname]:
                peaks[pname] = m
    return 0

cb = PROCESS_CB(process)
libjack.jack_set_process_callback(ctypes.c_void_p(client), cb, None)
libjack.jack_activate(ctypes.c_void_p(client))

for idx, pname in enumerate(src_ports):
    my_name = libjack.jack_port_name(ctypes.c_void_p(in_ports[idx]))
    libjack.jack_connect(ctypes.c_void_p(client), pname.encode(), my_name)

time.sleep(0.12)
libjack.jack_deactivate(ctypes.c_void_p(client))
libjack.jack_client_close(ctypes.c_void_p(client))

out = {}
for pname, val in peaks.items():
    db = 20.0 * math.log10(val) if val > 1e-5 else -72.0
    out[pname] = round(max(-72.0, min(0.0, db)), 1)

print(json.dumps(out))
