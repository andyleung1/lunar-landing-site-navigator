import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource

path = r'data\Site06_final_adj_5mpp_surf.tif'

with rasterio.open(path) as d:
    print("Size (pixels):     ", d.width, "x", d.height)
    print("Pixel size (m):    ", d.res)
    print("Area covered (km): ", round(d.width * d.res[0] / 1000, 1), "x",
          round(d.height * d.res[1] / 1000, 1))
    print("Projection:        ", d.crs)
    # Shrink big files so plotting is fast
    step = max(1, d.width // 1500)
    z = d.read(1, out_shape=(d.height // step, d.width // step), masked=True)
    extent = [d.bounds.left / 1000, d.bounds.right / 1000,
              d.bounds.bottom / 1000, d.bounds.top / 1000]

print("Height range:      ", float(z.min()), "to", float(z.max()))

zf = z.filled(float(z.mean()))  # fill missing pixels so shading works
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

im = ax1.imshow(zf, cmap="terrain", extent=extent)
fig.colorbar(im, ax=ax1, label="height")
ax1.set_title("Elevation (color = height)")

ls = LightSource(azdeg=315, altdeg=30)
ax2.imshow(ls.hillshade(zf, vert_exag=2), cmap="gray", extent=extent)
ax2.set_title("Shaded relief (looks like terrain)")

for ax in (ax1, ax2):
    ax.set_xlabel("x (km, polar stereographic)")
    ax.set_ylabel("y (km)")
plt.tight_layout()
plt.show()