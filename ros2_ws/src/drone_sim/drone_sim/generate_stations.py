import numpy as np

width = 8     
height = 4    
r = 1.0       

nx = int(np.ceil(width / (2*r)))
ny = int(np.ceil(height / (2*r)))

stations = []
for i in range(nx):
    for j in range(ny):
        x = r + i*2*r
        y = r + j*2*r
        stations.append({"base": (x, y, 1.0), "waypoints": []})

        num_wp = 8
        for k in range(num_wp):
            angle = 2*np.pi*k/num_wp
            wx = x + r*np.cos(angle)
            wy = y + r*np.sin(angle)
            wz = 1.0
            stations[-1]["waypoints"].append((wx, wy, wz))

for idx, s in enumerate(stations):
    print(f"Station {idx+1}: base={s['base']}")
    for wp in s["waypoints"]:
        print(f"   waypoint={wp}")
