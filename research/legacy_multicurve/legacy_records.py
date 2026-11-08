"""Forward-only, bounded legacy record inventory; not an Origin validator.

Independently authored from the documented control flow of official LabPlot
2.12.1's OriginAnyParser. Only the pinned fixture's simple annotation form is
supported. No byte-pattern search or resynchronization is used.
"""
from dataclasses import dataclass
import struct
from numeric_support import require

@dataclass(frozen=True)
class Frame:
    offset:int
    payload:bytes
    end:int
    @property
    def length(self):return len(self.payload)

def frame(blob,p):
    require(type(blob) is bytes and type(p) is int and 0<=p<=len(blob)-5,'truncated frame')
    n=struct.unpack_from('<I',blob,p)[0];end=p+5+n+bool(n)
    require(n<=16777216 and end<=len(blob) and blob[p+4]==10,'invalid framing')
    require(n==0 or blob[end-1]==10,'invalid payload delimiter')
    return Frame(p,blob[p+5:p+5+n],end)
def framed(b):
    require(type(b) is bytes and len(b)<16777216,'invalid payload')
    return struct.pack('<I',len(b))+b'\n'+b+(b'\n' if b else b'')
def name(b):
    require(b'\0' in b,'unterminated name')
    return b.split(b'\0')[0].decode('ascii')

class Walk:
    def __init__(self,b):self.b=b;self.p=17;self.frames=[]
    def take(self):
        require(len(self.frames)<10000,'frame cap')
        f=frame(self.b,self.p);self.p=f.end;self.frames.append(f);return f
    def list(self,width=1):
        items=[]
        while True:
            h=self.take()
            if not h.length:return items,h
            items.append([h]+[self.take() for _ in range(width-1)])
    def annotations(self):
        items=[]
        while True:
            h=self.take()
            if not h.length:return items,h
            a=self.take();b=self.take()
            require(not(a.length in (0x5e,10) and b.length==4),'annotation groups unsupported')
            require(a.length>0,'zero annotation first block unsupported')
            c=self.take();items.append([h,a,b,c])
    def run(self):
        require(self.b[:17]==b'CPYA 4,2878 724#\n','wrong legacy signature')
        self.global_header=self.take();require(self.global_header.length==75,'global header changed')
        require(not self.take().length,'global delimiter changed')
        self.datasets,self.datasets_end=self.list(3)
        self.windows=[]
        while True:
            h=self.take()
            if not h.length:self.windows_end=h;break
            require(h.length>=27,'short window header')
            w={'header':h,'name':name(h.payload[2:27]),'layers':[]};self.windows.append(w)
            while True:
                lh=self.take()
                if not lh.length:w['end']=lh;break
                layer={'header':lh};w['layers'].append(layer)
                layer['annotations'],layer['annotations_end']=self.annotations()
                layer['curves'],layer['curves_end']=self.list(2)
                for label in ('breaks','xaxis','yaxis','zaxis'):
                    layer[label],layer[label+'_end']=self.list()
        self.tail_start=self.p
        return self
