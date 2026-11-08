"""Run public tests in separate processes; generated fixtures are synthetic."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,'-B',str(root/'preview/make_fixtures.py')],check=True)
for optimized in (False,True):
    for suite in ('preview','native','research/ropj_readback','research/legacy_style_fields/tests','research/legacy_active_rows/tests','research/modern_binding_diagnostics/tests','research/modern_owner_walk/tests'):
        flags=['-B','-O'] if optimized else ['-B']
        subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s',str(root/suite),'-p','test_*.py','-v'],check=True,cwd=root)
