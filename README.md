# xpress8-python

Cython bindings for Microsoft's **Xpress8** compression library, as shipped in
the [Extensible Storage Engine (ESE)](https://github.com/microsoft/Extensible-Storage-Engine/tree/master/dev/ese/src/_xpress)
source tree. Released under the MIT License.

This is a sibling of [xpress9-python](https://github.com/Hugoberry/xpress9-python).
Xpress8 is the variant used by Power BI's `.pbix` file format and by various
Windows-internal data stores; it is *not* wire-compatible with Xpress9.

## Install

```bash
pip install xpress8
```

Or from source:

```bash
pip install -e .
```

## Usage

```python
from xpress8 import Xpress8

x = Xpress8()                       # max_original_size=65536, level=9

# Single-buffer round trip
compressed = x.compress(b"hello world " * 64)
restored   = x.decompress(compressed, len(b"hello world " * 64))

# PBIX-style chunked stream: each chunk has a 4-byte LE header
# (uncompressed_size: u16, compressed_size: u16).
plain = x.decompress_chunked(chunked_blob)
```

## Layout

```
xpress8.pyx              Cython wrapper class
xpress8.pxd              C declarations
src/Xpress8Wrapper.c     thin C shim over the ESE stream API
src/xencode.c            vendored from ESE _xpress
src/xdecode.c            vendored from ESE _xpress
src/xencode.i            vendored
src/xdecode.i            vendored
include/Xpress8Wrapper.h shim API
include/xpress.h         vendored
include/xprs.h           vendored
include/xpress_compat.h  small portability header for non-MSVC builds
```

## License

MIT. The vendored sources retain their original Microsoft copyright headers.
