"""Sierra Chart .scid (tick or 1s records, UTC) -> 5m OHLCV CSV in ET, bar-start labels (same format as bars/*_5m.csv)."""
import numpy as np, pandas as pd, struct, sys
rec=np.dtype([('t','<u8'),('o','<f4'),('h','<f4'),('l','<f4'),('c','<f4'),('n','<u4'),('v','<u4'),('bv','<u4'),('av','<u4')])
EPOCH=np.datetime64('1899-12-30T00:00:00','us')
def convert(src, out, start='2025-01-15'):
    hs=struct.unpack('<4xI',open(src,'rb').read(8))[0]
    m=np.memmap(src,dtype=rec,mode='r',offset=hs)
    t0=(np.datetime64(start,'us')-EPOCH).astype(np.int64)
    i0=np.searchsorted(m['t'],t0)
    parts=[]
    for a in range(i0,len(m),4_000_000):
        b=np.array(m[a:a+4_000_000])
        tick=(b['o']==0)|(np.abs(b['o'])>1e30)   # Sierra marks single-trade records with Open=0 or -1.999e37 (High/Low = ask/bid)
        o=np.where(tick,b['c'],b['o']); h=np.where(tick,b['c'],b['h']); l=np.where(tick,b['c'],b['l']); c=b['c']
        ok=(c>0)&(h>=l)&(l>0)
        ts=(EPOCH+b['t'][ok].astype('timedelta64[us]'))
        df=pd.DataFrame({'Open':o[ok],'High':h[ok],'Low':l[ok],'Close':c[ok],'Volume':b['v'][ok].astype('int64')},index=pd.DatetimeIndex(ts).tz_localize('UTC'))
        g=df.resample('5min',label='left',closed='left').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        parts.append(g)
    d=pd.concat(parts)
    d=d.groupby(level=0).agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'})   # chunk seams
    # drop isolated bad prints: bar extremes > 3% from the bar's close
    bad=((d.High/d.Close-1).abs()>0.03)|((d.Low/d.Close-1).abs()>0.03)
    d=d[~bad]
    d.index=d.index.tz_convert('America/New_York'); d.index.name='time'
    d.to_csv(out)
    print(src, '->', out, len(d), d.index.min(), d.index.max(), 'dropped bad', int(bad.sum()))
if __name__=='__main__':
    convert(sys.argv[1], sys.argv[2])
