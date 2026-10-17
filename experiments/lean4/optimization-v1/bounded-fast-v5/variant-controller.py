"""Apply the retained whole-process Lean protocol to an immutable variant build."""
import argparse
import json
from pathlib import Path
import shutil
import sys

import lean_run as protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-report', type=Path, required=True)
    args, forwarded = parser.parse_known_args()
    build_path = args.build_report.resolve()
    build = json.loads(build_path.read_text())
    assert build['status'] == 'COMPILED_AWAITING_CONFORMANCE'
    assert all(protocol.sha(protocol.ROOT / name) == digest for name, digest in build['sources'].items())
    assert all(protocol.sha(p['binary']) == p['binary_sha256'] for p in build['profiles'].values())
    protocol.SOURCE = Path(build['source_directory'])
    protocol.BUILD = Path(build['build_directory'])
    output_index = forwarded.index('--output')
    output = Path(forwarded[output_index + 1]).resolve()
    if '--benchmarks' not in forwarded:
        assert set(build['profiles']) == set(protocol.FULL)
    else:
        selected = forwarded[forwarded.index('--benchmarks') + 1:]
        selected = selected[:next((i for i, value in enumerate(selected) if value.startswith('--')), len(selected))]
        assert selected and set(selected) <= set(build['profiles'])
    sys.argv = [str(Path(protocol.__file__)), *forwarded]
    try:
        protocol.main()
    finally:
        if (output / 'report.json').is_file():
            provenance = {
                'schema': 'lean-variant-execution-provenance.v1',
                'build_report': str(build_path),
                'build_report_sha256': protocol.sha(build_path),
                'variant_controller_sha256': protocol.sha(__file__),
                'protocol_controller_sha256': protocol.sha(protocol.__file__),
                'protocol_overrides': {
                    'SOURCE': str(protocol.SOURCE),
                    'BUILD': str(protocol.BUILD),
                },
                'timing_and_output_validation_logic_changed': False,
            }
            (output / 'variant-controller.json').write_text(json.dumps(provenance, indent=2) + '\n')
            shutil.copyfile(__file__, output / 'variant-controller.py')
            shutil.copyfile(protocol.__file__, output / 'protocol-controller.py')


if __name__ == '__main__':
    main()
