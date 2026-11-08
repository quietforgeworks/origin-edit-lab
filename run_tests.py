"""Run public tests in separate processes; generated fixtures are synthetic."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,'-B',str(root/'preview/make_fixtures.py')],check=True)
for optimized in (False,True):
    # Keep frozen supplements in separate processes: some module/test names overlap.
    for suite in ('preview','native','research/ropj_readback','research/legacy_style_fields/tests','research/legacy_active_rows/tests','research/modern_binding_diagnostics/tests','research/modern_owner_walk/tests','research/legacy_allocation/tests','research/legacy_multicurve/tests','research/modern_native_binding','research/modern_native_scalar/tests'):
        flags=['-B','-O'] if optimized else ['-B']
        subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s',str(root/suite),'-p','test_*.py','-v'],check=True,cwd=root)

    # Repository-only bridges leave reviewed scientific modules/tests unchanged.
    for supplement in ('custom', 'multicurve-review'):
        subprocess.run([sys.executable,*flags,str(root/'research/run_native_data_tests.py'),'--suite',supplement],check=True,cwd=root)
    subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s',str(root/'research'),'-p','test_native_data_packaging.py','-v'],check=True,cwd=root)
