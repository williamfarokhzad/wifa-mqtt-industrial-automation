# Diagram sources

These original SVG drawings reproduce the synthetic times and temperature in `examples/retained-then-live.json`. Edit them as text or in Inkscape. They do not show a physical device.

To reproduce the exports, install Inkscape and Pillow on a design workstation (the lab itself needs neither):

```sh
inkscape --export-filename=/tmp/mqtt-retained-timeline.png mqtt-retained-timeline.svg
inkscape --export-filename=/tmp/mqtt-freshness-tick.png mqtt-freshness-tick.svg
python3 -c "from PIL import Image; from pathlib import Path; names=('mqtt-retained-timeline','mqtt-freshness-tick'); [Image.open(Path('/tmp')/(n+'.png')).save(n+'.webp',quality=86,method=6) for n in names]"
```
