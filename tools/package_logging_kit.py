"""Package only the explicit logging kit files, never logs or local environments."""
import hashlib
import json
import zipfile
from pathlib import Path


def main():
    workspace = Path(__file__).resolve().parents[3]
    root = workspace / 'Documents' / 'GROUP LOGGING KIT'
    tools = Path(__file__).resolve().parent
    sources = ['capture_telemetry.py', 'clock_reference.py', 'timing_report.py']
    (root / 'tools').mkdir(exist_ok=True)
    for name in sources:
        (root / 'tools' / name).write_bytes((tools / name).read_bytes())
    timing = (workspace / 'Documents' / 'CART TIMING VERIFICATION PLAN.md').read_text(encoding='utf-8')
    timing = timing.replace('python tools/', '.\\.venv\\Scripts\\python.exe tools/')
    timing = ('# Running the timing checks from this kit\n\n'
              'The coordinator leads these checks. After SETUP completes, open PowerShell in this extracted kit folder. '
              'Commands below use its local Python environment.\n\n' + timing)
    (root / 'TIMING GUIDE.md').write_text(timing, encoding='utf-8')
    (root / 'ADMIN ACCESS GUIDE.md').write_bytes((tools.parent / 'docs' / 'ADMIN_ACCESS.md').read_bytes())
    files = ['SETUP.cmd', 'START RECORDING.cmd', 'setup_logging.py', 'record.py', 'requirements.txt',
             'START HERE.md', 'RECORDING ASSIGNMENTS.md', 'TIMING GUIDE.md', 'ADMIN ACCESS GUIDE.md', 'verify_kit.py']
    files += ['tools/' + name for name in sources]
    manifest = dict(version='2026-10-27-firmware-priorities-1-2', hardware_verified=False,
                    note='Software checks only; verify actual laptops, firmware, clocks and endpoint coverage in the group pilot.',
                    sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files})
    (root / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    archive = workspace / 'Documents' / 'GROUP LOGGING KIT.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in files + ['MANIFEST.json']:
            zipped.write(root / name, 'GROUP LOGGING KIT/' + name)
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        for name in files:
            assert hashlib.sha256(zipped.read('GROUP LOGGING KIT/' + name)).hexdigest() == manifest['sha256'][name]
    print(f'Packaged and verified {len(files) + 1} files: {archive}')


if __name__ == '__main__':
    main()
