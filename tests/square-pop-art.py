"""Verify the AirBoat-only consolidation and the non-geometric silly repair."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageSequence

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('square_builder',ROOT/'scripts/build-square-pop-pack.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
manifest=json.loads((ROOT/'assets/square-pop/manifest.json').read_bytes())
binary=(ROOT/'assets/square-pop/square-pop.afm').read_bytes()
source=ROOT/'output/imagegen/airboat-square-pop-20261124/gif/silly.gif'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='3d232b171b252863aa92f114b27adc632e33e478734981bf07c18dfc163a95e6'

cache={}
def mask(ref):
    out=np.zeros((480,480),np.uint8)
    if ref is None:
        return out
    i,x,y,r,b,flip=ref
    sprite=manifest['sprites'][i]
    if i not in cache:
        values=[]
        at=16+sprite['offset'];end=at+sprite['bytes']
        while at<end:
            token=binary[at];at+=1
            value,count=token>>4,(token&15)+1
            if count==16:
                count+=binary[at];at+=1
            values.extend([value]*count)
        cache[i]=np.array(values,np.uint8).reshape((sprite['h'],sprite['w']))
    values=cache[i][:,::-1] if flip else cache[i]
    out[y:b,x:r]=values
    return out

with Image.open(source) as image:
    old=[builder.separate(f.convert('RGB')) for f in ImageSequence.Iterator(image)]
    image.seek(0)
    current=[builder.separate(f.convert('RGBA')) for f in ImageSequence.Iterator(image)]
    delays=[]
    for i in range(image.n_frames):
        image.seek(i);delays.append(image.info.get('duration',90))
for a,b in zip(old,current):
    assert np.array_equal(a[0],b[0]) and np.array_equal(a[1],b[1]),'Source eye geometry changed'

fields=[(builder.distance(w),builder.distance(p)) for w,p,_ in old]
duration=sum(delays)
clip=manifest['clips']['silly']
assert clip['color']=='#28cf60'
for i,frame in enumerate(clip['keyframes']):
    ms=i*40
    if ms<=duration:
        pos=min(len(old)-1,ms/max(1,duration-delays[-1])*(len(old)-1))
        a=min(len(old)-1,int(pos));b=min(len(old)-1,a+1);u=pos-a
        expected=[fields[a][j]*(1-u)+fields[b][j]*u for j in range(2)]
    else:
        u=builder.ease((ms-duration)/440)
        expected=[fields[-1][j]*(1-u)+fields[0][j]*u for j in range(2)]
    if i==len(clip['keyframes'])-1:
        expected=fields[0]
    for layer in range(2):
        assert np.array_equal(mask(frame['layers'][layer]),builder.coverage(expected[layer])),f'Performance changed: {i}/{layer}'
for frame in clip['keyframes']+clip['entry_keyframes']+clip['exit_keyframes']:
    assert frame['accent'] is None,'Green matte fragments remain'
assert len(manifest['clips'])==21 and len(manifest['clips'])+len(manifest['aliases'])==29
assert set(manifest['aliases'])=={'neutral','sleepy','laughing','crying','question','insert','delicious','eat'}
result={'status':'passed','source_frames':len(old),'unchanged_performance_frames':len(clip['keyframes']),
        'unchanged_eye_layers':len(clip['keyframes'])*2,'background':'#28cf60','green_matte_accents':0,
        'unique_performances':21,'semantic_entries':29,'pack_sha256':manifest['binary_sha256']}
out=ROOT/'.test-output/square-pop/art-validation.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
