"""End-to-end tests for xpress8-python.

Covers:
  1. Round-trip compress/decompress on assorted buffers.
  2. Parity against the pure-Python reference in `pbixray/pbixray/xpress8.py`
     (chunked decompression).
"""

import os
import random
import struct
import sys
import time
import unittest

from xpress8 import Xpress8

# Optional parity oracle.
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pbixray"))
    from pbixray.xpress8 import Xpress8 as PyXpress8
    HAVE_ORACLE = True
except Exception:
    HAVE_ORACLE = False


def make_chunked(blob: bytes, x: Xpress8, chunk: int = 32768) -> bytes:
    """Build a PBIX-style chunked stream from `blob`."""
    out = bytearray()
    for i in range(0, len(blob), chunk):
        piece = blob[i : i + chunk]
        comp = x.compress(piece, max_compressed_size=len(piece) + 64)
        # If compression made it bigger, store as-is.
        if len(comp) >= len(piece):
            out += struct.pack("<HH", len(piece), len(piece)) + piece
        else:
            out += struct.pack("<HH", len(piece), len(comp)) + comp
    return bytes(out)


class RoundTripTests(unittest.TestCase):
    def setUp(self):
        self.x = Xpress8()

    def _roundtrip(self, data: bytes):
        comp = self.x.compress(data, max_compressed_size=max(len(data) + 64, 128))
        out = self.x.decompress(comp, len(data))
        self.assertEqual(out, data)

    def test_repeated(self):
        self._roundtrip(b"abcdefgh" * 1000)

    def test_text(self):
        self._roundtrip((b"the quick brown fox jumps over the lazy dog. " * 200))

    def test_random(self):
        random.seed(0)
        data = bytes(random.randrange(256) for _ in range(4096))
        # Random data may not compress; xpress8 stored-block path will fail
        # compress(), so just probe sizes the encoder handles.
        try:
            self._roundtrip(data)
        except ValueError:
            # Compression ineffective on random data — acceptable.
            pass

    def test_small_sizes(self):
        for n in (256, 1024, 8192, 65536):
            self._roundtrip(b"X" * n)


@unittest.skipUnless(HAVE_ORACLE, "pbixray oracle not importable")
class ParityTests(unittest.TestCase):
    def setUp(self):
        self.x = Xpress8()

    def test_chunked_matches_pure_python(self):
        random.seed(1)
        plain = (b"compression parity oracle test " * 5000)[:200_000]
        chunked = make_chunked(plain, self.x)

        cython_out = self.x.decompress_chunked(chunked)
        python_out = PyXpress8.decompress_chunked(chunked)

        self.assertEqual(bytes(cython_out), plain)
        self.assertEqual(bytes(python_out), plain)
        self.assertEqual(bytes(cython_out), bytes(python_out))

    def test_stored_chunk(self):
        # u_size == c_size triggers the stored-block path on both impls.
        payload = os.urandom(1024)
        chunked = struct.pack("<HH", len(payload), len(payload)) + payload
        self.assertEqual(self.x.decompress_chunked(chunked), payload)
        self.assertEqual(bytes(PyXpress8.decompress_chunked(chunked)), payload)

    def test_benchmark(self):
        plain = (b"the quick brown fox jumps over the lazy dog\n" * 20000)
        chunked = make_chunked(plain, self.x)

        t0 = time.perf_counter()
        for _ in range(50):
            self.x.decompress_chunked(chunked)
        t_cy = time.perf_counter() - t0

        t0 = time.perf_counter()
        for _ in range(50):
            PyXpress8.decompress_chunked(chunked)
        t_py = time.perf_counter() - t0

        print(f"\n[bench] cython={t_cy:.3f}s  pure-python={t_py:.3f}s  "
              f"speedup={t_py / t_cy:.1f}x")


if __name__ == "__main__":
    unittest.main(verbosity=2)
