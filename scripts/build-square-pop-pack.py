"""Build the independent Square Pop AFM candidate from the generated native GIFs."""
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageSequence
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'output/imagegen/airboat-square-pop-20261124'
DEST = ROOT / 'assets/square-pop'
FPS = 25
TRANSITION_FRAMES = 19
AIRBOAT_ALIASES = {
    'laughing':'happy', 'crying':'sad', 'question':'silly', 'insert':'silly',
    'delicious':'funny', 'eat':'funny'
}
AIRBOAT_ALIAS_KEYS = set(AIRBOAT_ALIASES)


def ease(value):
    value = min(1,max(0,value))
    return value*value*(3-2*value)


def load_builder():
    spec=importlib.util.spec_from_file_location('square_pop_sprites',ROOT/'scripts/build-optimized-expressions.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def keep_large(mask, limit=2, minimum=350):
    labels,n=ndi.label(mask)
    areas=np.bincount(labels.ravel())
    ids=[int(i) for i in np.argsort(areas[1:])[::-1]+1 if areas[i]>=minimum][:limit]
    return np.isin(labels,ids) if ids else np.zeros_like(mask)


def separate(image):
    rgba=np.asarray(image.convert('RGBA'),dtype=np.uint8)
    a=rgba[:,:,:3].astype(np.int16)
    visible=rgba[:,:,3]>=128
    high,low=a.max(2),a.min(2)
    white=(low>232)&(high-low<26)&visible
    shapes=keep_large(white)
    full=ndi.binary_fill_holes(shapes)
    dark=(high<28)&(high-low<16)&visible
    labels,n=ndi.label(dark)
    areas=np.bincount(labels.ravel())
    edge=set(np.r_[labels[0],labels[-1],labels[:,0],labels[:,-1]])
    nearby=ndi.binary_dilation(full,iterations=6)
    eyes=np.zeros_like(shapes)
    for i in range(1,n+1):
        if i not in edge and 25<=areas[i]<=14000 and np.count_nonzero((labels==i)&nearby)>8:
            eyes|=labels==i
    full=ndi.binary_fill_holes(shapes|eyes)
    pupil=(dark&full)|eyes
    pupil=ndi.binary_opening(pupil,iterations=1)

    # Keep colored pixel decorations, excluding the original drifting background.
    background=np.median(a[np.r_[np.ones((38,480),bool),np.zeros((404,480),bool),np.ones((38,480),bool)]],axis=0)
    contrast=np.linalg.norm(a-background,axis=2)
    colorful=(high-low>55)&(contrast>80)&visible&(~ndi.binary_dilation(full,iterations=3))
    colorful[:65]=False
    colorful[402:]=False
    marks,n=ndi.label(colorful)
    areas=np.bincount(marks.ravel())
    allowed=[i for i in range(1,n+1) if 8<=areas[i]<=1800]
    accent=np.zeros((480,480,4),np.uint8)
    if allowed:
        mask=np.isin(marks,allowed)
        accent[:,:,:3]=np.clip(a,0,255).astype(np.uint8)
        accent[:,:,3]=mask.astype(np.uint8)*255
    return full,pupil,Image.fromarray(accent)


def distance(mask):
    if not mask.any():
        return np.full(mask.shape,1000,dtype=np.float32)
    return (ndi.distance_transform_edt(~mask)-ndi.distance_transform_edt(mask)).astype(np.float32)


def coverage(field):
    return np.rint(np.clip(.5-field/1.55,0,1)*15).astype(np.uint8)


def make_ref(values,pool):
    ys,xs=np.where(values)
    if not len(xs):
        return None
    box=(int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1))
    return pool.add(values[box[1]:box[3],box[0]:box[2]],box,None)


def idle_layers(white,pupil,pool):
    # Store one eye and its exact reflection, retaining independent positions.
    left=np.zeros((480,480),bool);left[:,:240]=True
    return [make_ref(values*side,pool) for side in (left,~left) for values in (white,pupil)]


def read_default():
    """Use the exact, user-approved soft-square renderer's A4 layer export."""
    metadata=json.loads((ART/'inputs/soft-square-idle.json').read_bytes())
    binary=(ART/'inputs'/metadata['binary']).read_bytes()
    if hashlib.sha256(binary).hexdigest()!=metadata['sha256']:
        raise ValueError('The accepted idle layer export does not match its receipt')
    renderer=ROOT/'docs/product/expression-square-idle.js'
    if hashlib.sha256(renderer.read_bytes()).hexdigest()!=metadata['renderer_sha256']:
        raise ValueError('Re-export the accepted idle after changing its renderer')
    frames=np.frombuffer(gzip.decompress(binary),np.uint8).reshape((metadata['frames'],2,480,480))
    if metadata['fps']!=FPS or frames.max()>15:
        raise ValueError('Unexpected accepted-idle sampling or coverage')
    for white,pupil in frames:
        if not np.array_equal(white,white[:,::-1]) or not np.array_equal(pupil,pupil[:,::-1]):
            raise ValueError('The accepted default must be exactly symmetric')
    beats=[(560,'瞳孔先转'),(1560,'慢眨一下'),(1880,'睁眼回弹'),(2640,'看另一侧'),
           (4080,'双眨·第一下'),(4560,'双眨·第二下'),(5360,'呼吸回稳')]
    return [(f[0],f[1]) for f in frames],beats,metadata['sha256']


def eye_pairs(whites,pupils):
    """Use the eye's actual connected region, not x=240, where possible."""
    labels,n=ndi.label(whites>=8)
    areas=np.bincount(labels.ravel())
    ids=[int(i) for i in np.argsort(areas[1:])[::-1]+1 if areas[i]>500]
    if len(ids)>=2 and areas[ids[1]]>.13*areas[ids[0]]:
        centers=[np.mean(np.where(labels==i)[1]) for i in ids[:2]]
        ordered=[i for _,i in sorted(zip(centers,ids[:2]))]
        # Assign the tiny antialiased fringe to its closest eye.
        fields=[ndi.distance_transform_edt(labels!=i) for i in ordered]
        owner=fields[0]<=fields[1]
    else:
        dots,n=ndi.label(pupils>=8)
        sizes=np.bincount(dots.ravel())
        chosen=[int(i) for i in np.argsort(sizes[1:])[::-1]+1 if sizes[i]>50][:2]
        centers=sorted(float(np.mean(np.where(dots==i)[1])) for i in chosen)
        columns=np.count_nonzero(whites>=8,axis=0)
        lo,hi=(round(centers[0]+9),round(centers[1]-9)) if len(centers)==2 else (180,300)
        if hi<=lo:
            lo,hi=180,300
        local=columns[lo:hi]
        candidates=np.flatnonzero(local<=local.min()+2)+lo
        midpoint=sum(centers)/2 if len(centers)==2 else 240
        split=int(candidates[np.argmin(np.abs(candidates-midpoint))])
        owner=np.indices(whites.shape)[1]<split
    return [(whites*owner,pupils*owner),(whites*(~owner),pupils*(~owner))]


def profile(mask):
    ys,xs=np.where(mask)
    if not len(xs):
        return None
    box=np.array((xs.min(),ys.min(),xs.max()+1,ys.max()+1),float)
    cropped=mask[int(box[1]):int(box[3]),int(box[0]):int(box[2])]
    normalized=np.asarray(Image.fromarray(cropped*17).resize((192,192),Image.Resampling.LANCZOS))>=128
    return box,distance(normalized)


def shape_between(a,b,u,fallback):
    if not a and not b:
        return np.zeros((480,480),np.uint8)
    if not a:
        field=b[1];other=np.array([fallback[0],fallback[1],fallback[0]+1,fallback[1]+1])
        box=other*(1-u)+b[0]*u
    elif not b:
        field=a[1];other=np.array([fallback[0],fallback[1],fallback[0]+1,fallback[1]+1])
        box=a[0]*(1-u)+other*u
    else:
        box=a[0]*(1-u)+b[0]*u
        field=a[1]*(1-u)+b[1]*u
    x,y,r,bottom=np.rint(box).astype(int)
    x,y=max(0,x),max(0,y);r,bottom=min(480,max(x+1,r)),min(480,max(y+1,bottom))
    norm=Image.fromarray(coverage(field)*17).resize((r-x,bottom-y),Image.Resampling.LANCZOS)
    out=np.zeros((480,480),np.uint8)
    out[y:bottom,x:r]=np.rint(np.asarray(norm,dtype=np.float32)/17).astype(np.uint8)
    return out


def transition(start,target,accent,pool):
    before,after=eye_pairs(*start),eye_pairs(*target)
    profiles=[([profile(m) for m in a],[profile(m) for m in b]) for a,b in zip(before,after)]
    poses=[]
    for i in range(TRANSITION_FRAMES):
        t=i/(TRANSITION_FRAMES-1)
        if not i:
            white,black=start
        elif i==TRANSITION_FRAMES-1:
            white,black=target
        else:
            white=np.zeros((480,480),np.uint8);black=np.zeros_like(white)
            # Quintic timing eases speed and acceleration at both ends.
            motion=lambda v:(v**3*(v*(v*6-15)+10))
            u=motion(t)
            gaze=motion(min(1,t*1.07))
            for a,b in profiles:
                eye_box=b[0][0] if b[0] else a[0][0]
                center=((eye_box[0]+eye_box[2])/2,(eye_box[1]+eye_box[3])/2)
                white=np.maximum(white,shape_between(a[0],b[0],u,center))
                black=np.maximum(black,shape_between(a[1],b[1],gaze,center))
        level=ease((t-.25)/.75)
        overlay=accent.copy()
        overlay.putalpha(overlay.getchannel('A').point(lambda v:round(v*level)))
        poses.append({'layers':[make_ref(white,pool),make_ref(black,pool),None,None],
                      'accent':pool.add_accent(overlay.quantize(colors=32,method=Image.Quantize.FASTOCTREE).convert('RGBA'))})
    return poses


def build():
    spec=json.loads((ART/'study.json').read_bytes())
    roles=[r for g in spec['groups'] for r in g['roles'] if r['key'] not in AIRBOAT_ALIAS_KEYS]
    aliases={**spec['aliases'],**AIRBOAT_ALIASES}
    builder=load_builder()
    pool=builder.Sprites()
    clips,beats,sources={}, {}, {}
    default,default_beats,default_hash=read_default()
    base=default[0]
    for folder in ('png','preview'):
        (ART/folder).mkdir(exist_ok=True)
    still=Image.new('RGB',(480,480),'#28cf60')
    still.paste('white',(0,0),Image.fromarray(base[0]*17))
    still.paste('black',(0,0),Image.fromarray(base[1]*17))
    still.save(ART/'png/idle.png')
    for role in roles:
        key=role['key']
        if key=='idle':
            frames=[{'layers':idle_layers(w,p,pool),'accent':None} for w,p in default]
            entry=[frames[0]]*TRANSITION_FRAMES
            clips[key]={'color':'#28cf60','body_frames':len(frames),'keyframes':frames,
                        'entry_keyframes':entry,'exit_keyframes':entry}
            beats[key]=default_beats
            sources[key]=default_hash
            continue
        source=ART/'gif'/f'{key}.gif'
        with Image.open(source) as image:
            mode='RGBA' if key=='silly' else 'RGB'
            native=[separate(f.convert(mode)) for f in ImageSequence.Iterator(image)]
            delays=[]
            for i in range(image.n_frames):
                image.seek(i);delays.append(image.info.get('duration',90))
        if key=='silly':
            # This source has no intentional decorations. Its green fringe was
            # previously mistaken for accents, producing flickering matte chips.
            native=[(w,p,Image.new('RGBA',(480,480))) for w,p,_ in native]
        count=len(native)
        fields=[(distance(w),distance(p)) for w,p,_ in native]
        duration=sum(delays)
        frames=[]
        # Native keys remain in the same order. 25 fps signed-distance sampling
        # changes a shape continuously, without cross-faded pupil ghosts.
        body_frames=round((duration+440)/40)+1
        for i in range(body_frames):
            ms=i*40
            if ms<=duration:
                # Two extra samples at the end close the art loop to its first pose.
                pos=min(count-1,ms/max(1,duration-delays[-1])*(count-1))
                a=min(count-1,int(pos));b=min(count-1,a+1);u=pos-a
                white=fields[a][0]*(1-u)+fields[b][0]*u
                pupil=fields[a][1]*(1-u)+fields[b][1]*u
                accent=Image.blend(native[a][2],native[b][2],u)
            else:
                u=ease((ms-duration)/440)
                white=fields[-1][0]*(1-u)+fields[0][0]*u
                pupil=fields[-1][1]*(1-u)+fields[0][1]*u
                accent=Image.blend(native[-1][2],native[0][2],u)
            if i==body_frames-1:
                white,pupil=fields[0]
                accent=native[0][2]
            # 4 bit edge coverage; the shared eye mask clips both pupils together
            # so a rectangular eye is not cut at the screen center.
            whites,black=coverage(white),coverage(pupil)
            layers=[make_ref(whites,pool),make_ref(black,pool),None,None]
            accent=accent.quantize(colors=32,method=Image.Quantize.FASTOCTREE).convert('RGBA')
            frames.append({'layers':layers,'accent':pool.add_accent(accent)})
        target=(coverage(fields[0][0]),coverage(fields[0][1]))
        entry=transition(base,target,native[0][2],pool)
        entry[0]=clips['idle']['keyframes'][0]
        entry[-1]=frames[0]
        # Reverse the same geometric path, so both boundaries are exact.
        exit_path=list(reversed(entry))
        color='#28cf60' if key=='silly' else spec['palette'][role['palette']]
        clips[key]={'color':color,'body_frames':len(frames),'keyframes':frames,
                    'entry_keyframes':entry,'exit_keyframes':exit_path}
        beats[key]=[(round(duration*.18/40)*40,'预动'),(round(duration*.40/40)*40,'夸张主动作'),
                    (round(duration*.64/40)*40,'停顿与余拍'),(round(duration/40)*40,'回到起势')]
        sources[key]=hashlib.sha256(source.read_bytes()).hexdigest()
        print(key,len(frames),'frames',flush=True)
    payload=b'AFM1'+struct.pack('<III',1,len(pool.rows),len(pool.payload))+pool.payload
    pack={'format':'airboat.layered-face.v1','variant':'square-pop','canvas':480,'fps':FPS,'alpha_levels':16,
          'transition_frames':TRANSITION_FRAMES,'authored_transitions':True,'base':'idle','sprites':pool.rows,'clips':clips,'aliases':aliases,
          'binary':'square-pop.afm','binary_bytes':len(payload),'binary_sha256':hashlib.sha256(payload).hexdigest(),
          'catalog_bytes':0,'clip_pupils':True,'exit_from_last':True,'beats':beats,'art_sources_sha256':sources,
          'sharing':{'references':pool.references,'unique_sprites':len(pool.rows),
                     'reflected_reuse_hits':pool.reflection_hits,'reflected_reuse_bytes':pool.saved_by_reflection},
          'default_source_sha256':default_hash,
          'review':'AirBoat semantic aliases share canonical performances; transparent GIF pixels excluded; silly uses fixed idle green'}
    for _ in range(8):
        catalog=json.dumps(pack,ensure_ascii=False,separators=(',',':'))+'\n';pack['catalog_bytes']=len(catalog.encode())
    catalog=json.dumps(pack,ensure_ascii=False,separators=(',',':'))+'\n'
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'square-pop.afm').write_bytes(payload)
    (DEST/'manifest.json').write_text(catalog,encoding='utf-8',newline='\n')
    js='// Square Pop candidate; generated by build-square-pop-pack.py.\nwindow.AIRBOAT_SQUARE_PACK='+catalog.strip()+';\n'
    js+='window.AIRBOAT_SQUARE_PACK.payload="'+base64.b64encode(payload).decode()+'";\n'
    (ROOT/'docs/product/expression-square-data.js').write_text(js,encoding='utf-8',newline='\n')
    print(json.dumps({'status':'built','clips':len(clips),'bytes':len(payload)+len(catalog.encode()),'sha256':pack['binary_sha256']}))


if __name__=='__main__':
    build()
