"""Generate binary64 formatting cases using Python's independent float formatter."""
import math
from pathlib import Path
import random
import struct


def vectors():
    values = [0.0, -0.0, 0.5, -0.5, 1.5, 2.5, -2.5, 1.25, 1.375,
              math.ulp(0.0), -math.ulp(0.0), 1e-308, -1e-308,
              1.7976931348623157e308, -1.7976931348623157e308]
    for value in [0.5, 1.25, 2.675, 999.5, 1e-9, 1e18]:
        values.extend([math.nextafter(value, -math.inf), value,
                       math.nextafter(value, math.inf)])
    generator = random.Random(20261014)
    while len(values) < 256:
        value = struct.unpack('>d', generator.getrandbits(64).to_bytes(8, 'big'))[0]
        if math.isfinite(value):
            values.append(value)
    for value in values:
        for digits in [0, 1, 2, 6, 9, 18]:
            yield struct.pack('>d', value).hex(), str(digits), format(value, f'.{digits}f')


if __name__ == '__main__':
    path = Path(__file__).with_name('format-vectors.tsv')
    with path.open('x') as stream:
        for row in vectors():
            stream.write('\t'.join(row) + '\n')
