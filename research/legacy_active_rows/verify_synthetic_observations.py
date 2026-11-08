"""Recheck published toy-data application observations without any OPJ fixture.

This checks retained actual-app evidence only; it does not rerun LabPlot and
does not verify Origin acceptance or whole-project preservation by itself.
"""
from pathlib import Path
import csv,io,json,math,struct
ROOT=Path(__file__).resolve().parent
def need(ok,message):
    if not ok:raise ValueError(message)
def check(n):
    rows=list(csv.reader(io.StringIO((ROOT/'candidates'/f'raw{n}.csv').read_text(encoding='utf-8'),newline='')))
    need(rows[0]==['A','B'] and len(rows)==n+1,'bad toy CSV shape')
    expected=[[struct.pack('>d',float(v)).hex() for v in r] for r in rows[1:]]
    d=ROOT/'evidence/synthetic-observations'/f'active{n}'
    values=list(csv.DictReader(io.StringIO((d/'native-app-values.tsv').read_text(encoding='utf-8'),newline=''),delimiter='\t'))
    cells={(int(v['row']),int(v['column'])):v['hex_binary64'] for v in values}
    need(len(values)==len(cells)==100,'require 100 distinct allocated cells')
    for r in range(50):
        for c in range(2):
            bits=cells[(r,c)]
            need(bits==expected[r][c] if r<n else math.isnan(struct.unpack('>d',bytes.fromhex(bits))[0]),'active bits or inactive missing values differ')
    curve=json.loads((d/'curve-observation.json').read_text())
    need(curve['curve_found'] and curve['signal_spy_valid'] and curve['x_bound'] and curve['y_bound'],'curve observation missing')
    need(curve['x_allocated_rows']==curve['y_allocated_rows']==50 and len(curve['rows'])==50,'wrong allocation')
    for r,cell in enumerate(curve['rows']):
        need(cell['row']==r and cell['x_bits']==cells[(r,0)] and cell['y_bits']==cells[(r,1)],'curve-bound cell identity/bits differ')
        need(cell['x_valid']==cell['y_valid']==(r<n) and not cell['x_masked'] and not cell['y_masked'],'curve-bound cell validity/mask differs')
    emissions=curve['point_signal_emissions'];need(len(emissions)>0,'no signal emission')
    for e in emissions:
        need((e['logical_point_count'],e['start_index'],e['end_index'])==(n,0,n-1),'wrong logical point count/range')
        need(e['logical_points_binary64']==expected,'render logical-point bits differ from CSV')
    return {'active_rows':n,'allocated_rows':50,'bit_exact_active_values':2*n,'missing_inactive_values':2*(50-n),'verified_curve_signals':len(emissions)}
if __name__=='__main__':print(json.dumps([check(n) for n in (7,49,50)],indent=2))
