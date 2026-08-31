from pathlib import Path
import subprocess, sys, yaml
ROOT=Path(__file__).resolve().parents[1]

# YAML parse
for p in ROOT.rglob('*.yaml'):
    yaml.safe_load(p.read_text(encoding='utf-8'))

# Python compile
subprocess.run([sys.executable,'-m','compileall','-q',str(ROOT)],check=True)
for d in list(ROOT.rglob('__pycache__')):
    import shutil; shutil.rmtree(d,ignore_errors=True)
for f in ROOT.rglob('*.pyc'):
    f.unlink(missing_ok=True)

# Public package must not contain common private/local project roots.
bad=[]
for p in ROOT.rglob('*'):
    if p == Path(__file__).resolve():
        continue
    if p.is_file() and p.suffix.lower() in {'.md','.yaml','.py','.txt'}:
        t=p.read_text(encoding='utf-8',errors='ignore')
        for token in ['/data66T/','/data/PublicBreastPathology/','/data/lvhongtai/']:
            if token in t: bad.append((str(p),token))
assert not bad,bad

# No private research binaries or generated caches in the public Skill.
forbidden_ext={'.svs','.ndpi','.mrxs','.dcm','.h5','.hdf5','.pt','.pth','.ckpt','.safetensors'}
for p in ROOT.rglob('*'):
    if p.is_file() and p.suffix.lower() in forbidden_ext:
        raise AssertionError(f'forbidden research/model artifact in release: {p}')
assert not list(ROOT.rglob('__pycache__')), 'release contains __pycache__'
assert not list(ROOT.rglob('*.pyc')), 'release contains pyc'
print('ACCEPTANCE_PASS')
