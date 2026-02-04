# Image Processor

Python script to process images from a folder and export them as `1920x1080` PNG files (`16:9`, landscape), preserving proportions (no distortion).

## Features

- Reads images from an input folder
- Creates an output subfolder (default: `png_1920x1080`)
- Resizes and fits images into `1920x1080` without stretching
- Centers image content
- Keeps empty areas transparent by default
- Optional solid background color (`--bg-color`)
- Optional custom output size (`--size`)
- Optional resize mode (`--resize-mode`: `fit` or `cover`)
- Optional recursive processing (`--recursive`) keeping subfolder structure
- Optional output format and quality (`--format`, `--quality`)
- Optional side-by-side mode for vertical images

## Requirements

- Python 3
- Pillow

Install Pillow:

```bash
pip install pillow
```

## Usage

```bash
py process_images.py "C:\path\to\input_folder"
```

### Arguments

- `input_dir`  
  Path to the folder containing images.

- `--output-dir-name`  
  Output subfolder name inside `input_dir`.  
  Default: `png_WIDTHxHEIGHT` (example: `png_1920x1080`, `png_2560x1080`)

- `--bg-color`  
  Background color. If omitted, background is transparent.  
  Accepted examples: `#C0714B`, `red`, `rgb(192,113,75)`

- `--size`  
  Custom output size in `WIDTHxHEIGHT` format.  
  Default: `1920x1080`  
  Example: `--size 2560x1440`

- `--recursive`  
  Processes subfolders recursively and preserves folder structure in output.

- `--resize-mode`  
  Resize behavior: `fit` (default) or `cover`.  
  `fit` keeps the whole image visible (with empty areas).  
  `cover` fills the full canvas and crops overflowing parts from center.

- `--format`  
  Output format: `png`, `jpg`/`jpeg`, `webp`.  
  Default: `png`

- `--quality`  
  Quality for `jpg`/`webp` output (`1-100`).  
  Default: `92`

- `--side-by-side-vertical`  
  Pairs vertical images in the same output image, using as many columns as fit
  for the selected output format.  
  If some verticals are left, they are exported as a partial group (or single centered image).

- `--side-by-side-vertical-cyclic`  
  Like `--side-by-side-vertical`, but avoids leftover verticals by reusing
  images from the beginning to fill the last group.

> Use only one of `--side-by-side-vertical` or `--side-by-side-vertical-cyclic`.

## Examples

Default (transparent background):

```bash
py process_images.py "C:\Users\you\Desktop\MyImages"
```

With solid background color:

```bash
py process_images.py "C:\Users\you\Desktop\MyImages" --bg-color "#C0714B"
```

Side-by-side vertical mode:

```bash
py process_images.py "C:\Users\you\Desktop\MyImages" --side-by-side-vertical
```

Cyclic side-by-side vertical mode with color:

```bash
py process_images.py "C:\Users\you\Desktop\MyImages" --side-by-side-vertical-cyclic --bg-color "red"
```

Custom size + dynamic side-by-side:

```bash
py process_images.py "C:\Users\you\Desktop\MyImages" --size 2560x1080 --side-by-side-vertical
```

Recursive + JPEG:

```bash
py process_images.py "C:\Users\you\Desktop\MyImages" --recursive --format jpg --quality 90 --bg-color "#111111"
```

Cover mode:

```bash
py process_images.py "C:\Users\you\Desktop\MyImages" --resize-mode cover --size 1920x1080
```
