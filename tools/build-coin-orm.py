"""Pack the coin's ambient occlusion, roughness and metalness maps into one texture.

Each of the three was its own 1024x1024 image holding a single grey value per
pixel, and the browser hands every one of them to the GPU as full RGBA, so the
coin was carrying six four-megabyte maps to describe three grey numbers.
MeshStandardMaterial already reads ambient occlusion from the red channel,
roughness from green and metalness from blue, which is the glTF ORM layout, so
one RGB image feeds all three slots. Half the width as well: the coin draws at
about 300 CSS pixels, so 512 is still more detail than any screen can show.

The encoding is lossless webp over values rounded to 32 levels a channel. Plain
lossless doubles the download, because three unrelated greys in one RGB pixel
defeat webp's cross channel prediction, and plain lossy is worse than it sounds:
metalness is a hard black and white mask, webp's lossy mode subsamples the blue
channel, and the mask edges came back off by up to 115 of 255. Rounding first
costs at most 4 of 255 on any pixel and compresses smaller than the three
separate maps it replaces.

Sources live in assets/coin-tex/src and are not loaded by the site.
Run: python tools/build-coin-orm.py
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'assets', 'coin-tex')
SRC = os.path.join(TEX, 'src')
SIZE = (512, 512)
STEP = 8  # 32 levels a channel


def channel(name):
    """One source map, greyscale and halved. The sources are grey already, so
    any channel of them carries the whole value."""
    im = Image.open(os.path.join(SRC, name)).convert('L').resize(SIZE, Image.LANCZOS)
    return im.point(lambda v: min(255, (v // STEP) * STEP + STEP // 2))


def main():
    for face in ('heads', 'tails'):
        packed = Image.merge('RGB', (
            channel(face + '-ao.webp'),     # aoMap reads .r
            channel(face + '-rough.webp'),  # roughnessMap reads .g
            channel(face + '-metal.webp'),  # metalnessMap reads .b
        ))
        out = os.path.join(TEX, face + '-orm.webp')
        packed.save(out, 'WEBP', lossless=True, method=6)
        print(face, packed.size, os.path.getsize(out), 'bytes ->', os.path.relpath(out, HERE))


if __name__ == '__main__':
    main()
