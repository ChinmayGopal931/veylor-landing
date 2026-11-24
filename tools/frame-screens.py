#!/usr/bin/env python3
"""Draws the app's captures inside a laptop and a phone, for the home page.

The captures are the app's own, from `scripts/figma-compare.sh widget` in its
repository, written at the screen's density (2x desktop, 3x phone). Never pass
one of a real wallet. It needs Pillow and NumPy, and writes three transparent
PNGs to --out:

    python3 tools/frame-screens.py --fonts <app>/assets/fonts \\
        --desktop desktop.png --phone home.png --token 0zkusdc.png --out .

Then, for each: cwebp -q 88 -alpha_q 95 -m 6 app-x.png -o art/app-x.webp
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import argparse, math, pathlib
import numpy as np
F = ''
def rr(size,box,r,fill=255):
    m=Image.new('L',size,0); ImageDraw.Draw(m).rounded_rectangle(box,radius=r,fill=fill); return m
def lin(size,stops,angle):
    """A linear gradient over size; stops: [(t,(r,g,b))], angle in degrees (0 = left to right)."""
    w,h=size; yy,xx=np.mgrid[0:h,0:w]; a=math.radians(angle)
    t=(xx*math.cos(a)+yy*math.sin(a)); t=(t-t.min())/(t.max()-t.min())
    out=np.zeros((h,w,3))
    for k in range(3): out[...,k]=np.interp(t,[s[0] for s in stops],[s[1][k] for s in stops])
    return Image.fromarray(out.astype('uint8'),'RGB')
def over(base,colour,mask):
    layer=Image.new('RGBA',base.size,colour+(255,) if len(colour)==3 else colour); layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask)); base.alpha_composite(layer)
def put(base,img,mask,xy=(0,0)):
    l=Image.new('RGBA',base.size,(0,0,0,0)); l.paste(img,xy); a=Image.new('L',base.size,0); a.paste(mask,(0,0)); l.putalpha(ImageChops.multiply(l.getchannel('A'),a)); base.alpha_composite(l)

def phone(src,dst,width):
    shot=Image.open(src).convert('RGB'); sw,sh=shot.size          # 1179 x 2556, at 3x
    bez,ring,pad=30,24,12
    W=sw+2*(bez+ring+pad); H=sh+2*(bez+ring+pad)
    out=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(out)
    x0=y0=pad; x1=W-pad-1; y1=H-pad-1; R=168+bez+ring
    # the buttons, behind the body
    for (bx,a,b) in ((0,430,520),(0,640,840),(0,890,1090)):
        d.rounded_rectangle((bx+1,a,pad+10,b),radius=5,fill=(128,128,134,255)); d.line((bx+3,a+6,bx+3,b-6),fill=(214,214,220,255),width=2)
    d.rounded_rectangle((W-pad-10,700,W-2,1010),radius=5,fill=(112,112,118,255)); d.line((W-4,706,W-4,1004),fill=(190,190,197,255),width=2)
    # the metal ring
    metal=lin((W,H),[(0,(236,236,240)),(0.1,(150,150,157)),(0.24,(206,206,212)),(0.42,(118,118,125)),(0.6,(176,176,183)),(0.78,(104,104,111)),(0.9,(198,198,205)),(1,(140,140,147))],62)
    put(out,metal,rr((W,H),(x0,y0,x1,y1),R))
    over(out,(255,255,255),ImageChops.subtract(rr((W,H),(x0+4,y0+4,x1-4,y1-4),R-4),rr((W,H),(x0+8,y0+8,x1-8,y1-8),R-8)).point(lambda v:int(v*0.5)))
    over(out,(40,40,44),ImageChops.subtract(rr((W,H),(x0,y0,x1,y1),R),rr((W,H),(x0+3,y0+3,x1-3,y1-3),R-3)).point(lambda v:int(v*0.75)))
    over(out,(26,26,28),rr((W,H),(x0+ring-5,y0+ring-5,x1-ring+5,y1-ring+5),R-ring+5))
    # the glass
    over(out,(0,0,0),rr((W,H),(x0+ring,y0+ring,x1-ring,y1-ring),R-ring))
    sx=x0+ring+bez; sy=y0+ring+bez
    put(out,shot,rr((W,H),(sx,sy,sx+sw-1,sy+sh-1),168),(sx,sy))
    # the island, its lens, and the status bar
    iw,ih=372,108; ix=sx+(sw-iw)//2; iy=sy+36
    over(out,(0,0,0),rr((W,H),(ix,iy,ix+iw,iy+ih),ih//2)); over(out,(255,255,255),ImageChops.subtract(rr((W,H),(ix,iy,ix+iw,iy+ih),ih//2),rr((W,H),(ix+2,iy+2,ix+iw-2,iy+ih-2),ih//2-2)).point(lambda v:int(v*0.07)))
    lx,ly,lr=ix+iw-58,iy+ih//2,17
    d=ImageDraw.Draw(out); d.ellipse((lx-lr,ly-lr,lx+lr,ly+lr),fill=(9,11,18,255)); d.ellipse((lx-8,ly-8,lx+8,ly+8),fill=(18,26,46,255)); d.ellipse((lx-6,ly-7,lx-1,ly-2),fill=(60,80,120,255))
    f=ImageFont.truetype(F+'Gotham-Medium.otf',48); d.text((sx+148,sy+66),'9:41',font=f,fill=(255,255,255,255),anchor='lt')
    bx=sx+sw-330; by=sy+66
    for k,hh in enumerate((14,21,28,36)): d.rounded_rectangle((bx+k*15,by+36-hh,bx+k*15+10,by+36),radius=3,fill=(255,255,255,255))
    wx,wy=bx+108,by+36
    for rad,wd in ((46,9),(30,9)): d.arc((wx-rad,wy-rad,wx+rad,wy+rad),225,315,fill=(255,255,255,255),width=wd)
    d.pieslice((wx-13,wy-13,wx+13,wy+13),225,315,fill=(255,255,255,255))
    ex,ey=bx+168,by+2
    d.rounded_rectangle((ex,ey,ex+76,ey+34),radius=11,outline=(255,255,255,120),width=3); d.rounded_rectangle((ex+6,ey+6,ex+70,ey+28),radius=6,fill=(255,255,255,255)); d.rounded_rectangle((ex+79,ey+11,ex+84,ey+23),radius=3,fill=(255,255,255,120))
    hw=420; d.rounded_rectangle((sx+(sw-hw)//2,sy+sh-36,sx+(sw+hw)//2,sy+sh-21),radius=8,fill=(255,255,255,215))
    out=out.resize((width,int(H*width/W)),Image.LANCZOS); out.save(dst); print(dst.split('/')[-1],out.size)

def laptop(src,dst,width):
    shot=Image.open(src).convert('RGB')
    W,H=2480,1500; out=Image.new('RGBA',(W,H),(0,0,0,0))
    lx0,ly0,lx1,ly1=250,14,W-250,1330
    # the lid: a bright edge, then black
    edge=lin((W,H),[(0,(214,214,220)),(0.25,(150,150,157)),(0.5,(196,196,203)),(0.8,(128,128,135)),(1,(190,190,197))],20)
    lid=rr((W,H),(lx0,ly0,lx1,ly1+60),54); put(out,edge,lid)
    over(out,(30,30,33),rr((W,H),(lx0+7,ly0+7,lx1-7,ly1+60),48)); over(out,(2,2,3),rr((W,H),(lx0+11,ly0+11,lx1-11,ly1+60),44))
    sx0,sy0,sx1,sy1=lx0+32,ly0+32,lx1-32,ly1-44; SW,SH=sx1-sx0,sy1-sy0
    # the wallpaper: night, a low sun, a horizon and a floor
    wp=lin((SW,SH),[(0,(10,2,8)),(0.45,(48,5,18)),(0.72,(120,10,28)),(0.74,(16,1,5)),(1,(4,0,2))],90).convert('RGBA')
    hz=int(SH*0.73)
    g=Image.new('L',(SW,SH),0); ImageDraw.Draw(g).ellipse((SW/2-760,hz-760,SW/2+760,hz+760),fill=170); g=g.filter(ImageFilter.GaussianBlur(170))
    l=Image.new('RGBA',(SW,SH),(255,46,62,255)); l.putalpha(g); wp.alpha_composite(l)
    sun=lin((SW,SH),[(0,(255,190,170)),(0.3,(255,120,110)),(0.6,(255,46,62)),(1,(190,12,32))],90)
    sr=470; m=Image.new('L',(SW,SH),0); dm=ImageDraw.Draw(m); dm.ellipse((SW/2-sr,hz-sr,SW/2+sr,hz+sr),fill=255)
    for (a,b) in ((0.36,0.385),(0.49,0.53),(0.62,0.68),(0.76,0.84)): dm.rectangle((0,hz-sr+sr*a,SW,hz-sr+sr*b),fill=0)
    dm.rectangle((0,hz,SW,SH),fill=0); s2=sun.crop((0,0,SW,SH)).convert('RGBA'); s2.putalpha(m); wp.alpha_composite(s2)
    fl=Image.new('RGBA',(SW,SH),(0,0,0,0)); df=ImageDraw.Draw(fl)
    for k in range(-40,41): df.line((SW/2+k*26,hz,SW/2+k*330,SH+120),fill=(255,60,76,105),width=2)
    yv=hz; step=5.0
    while yv<SH: df.line((0,yv,SW,yv),fill=(255,60,76,95),width=2); yv+=step; step*=1.34
    fl=fl.filter(ImageFilter.GaussianBlur(0.8)); wp.alpha_composite(fl)
    ImageDraw.Draw(wp).line((0,hz,SW,hz),fill=(255,150,155,255),width=3)
    # the menu bar
    bar=Image.new('RGBA',(SW,SH),(0,0,0,0)); ImageDraw.Draw(bar).rectangle((0,0,SW,40),fill=(6,1,4,150)); wp.alpha_composite(bar)
    dw=ImageDraw.Draw(wp); fb=ImageFont.truetype(F+'Gotham-Medium.otf',21); fr=ImageFont.truetype(F+'Gotham-Book.otf',21)
    dw.text((34,20),'Veylor',font=fb,fill=(255,255,255,245),anchor='lm'); dw.text((128,20),'File',font=fr,fill=(255,255,255,225),anchor='lm'); dw.text((190,20),'Window',font=fr,fill=(255,255,255,225),anchor='lm'); dw.text((292,20),'Help',font=fr,fill=(255,255,255,225),anchor='lm')
    dw.text((SW-34,20),'Fri Nov 20  9:41 AM',font=fr,fill=(255,255,255,235),anchor='rm')
    ex=SW-330; dw.rounded_rectangle((ex,12,ex+34,28),radius=5,outline=(255,255,255,190),width=2); dw.rounded_rectangle((ex+4,16,ex+26,24),radius=2,fill=(255,255,255,235)); dw.rounded_rectangle((ex+36,17,ex+38,23),radius=1,fill=(255,255,255,190))
    wx,wy=ex-34,27
    for rad in (16,10): dw.arc((wx-rad,wy-rad,wx+rad,wy+rad),225,315,fill=(255,255,255,235),width=3)
    dw.pieslice((wx-4,wy-4,wx+4,wy+4),225,315,fill=(255,255,255,235))
    # the window: its shadow, the app, an edge, the traffic lights
    ww=int(SW*0.82); wh=int(ww*shot.size[1]/shot.size[0]); wx0=(SW-ww)//2; wy0=40+(SH-40-wh)//2
    sh=Image.new('L',(SW,SH),0); ImageDraw.Draw(sh).rounded_rectangle((wx0,wy0+26,wx0+ww,wy0+wh+26),radius=26,fill=235); sh=sh.filter(ImageFilter.GaussianBlur(34))
    l=Image.new('RGBA',(SW,SH),(0,0,0,255)); l.putalpha(sh); wp.alpha_composite(l)
    win=shot.resize((ww,wh),Image.LANCZOS); wm=rr((ww,wh),(0,0,ww-1,wh-1),24); wp.paste(win,(wx0,wy0),wm)
    line=ImageChops.subtract(rr((SW,SH),(wx0,wy0,wx0+ww-1,wy0+wh-1),24),rr((SW,SH),(wx0+2,wy0+2,wx0+ww-3,wy0+wh-3),22)).point(lambda v:int(v*0.34))
    l=Image.new('RGBA',(SW,SH),(255,255,255,255)); l.putalpha(line); wp.alpha_composite(l)
    dw=ImageDraw.Draw(wp); k=ww/1000
    for n,c in enumerate(((255,95,87),(254,188,46),(40,200,64))):
        cx,cy,r=wx0+(34+n*20)*k,wy0+29*k,6.2*k; dw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=c+(255,))
    put(out,wp.convert('RGB'),rr((W,H),(sx0,sy0,sx1-1,sy1-1),16),(sx0,sy0))
    # the notch and its camera
    d=ImageDraw.Draw(out); nw=236; nx=W//2-nw//2
    over(out,(2,2,3),rr((W,H),(nx,sy0-20,nx+nw,sy0+36),14)); d=ImageDraw.Draw(out); d.ellipse((W//2-6,sy0+9,W//2+6,sy0+21),fill=(14,18,30,255)); d.ellipse((W//2-2,sy0+12,W//2+1,sy0+15),fill=(58,74,112,255))
    # the base
    by0=ly1; by1=by0+98
    base=Image.new('L',(W,H),0); db=ImageDraw.Draw(base); db.rounded_rectangle((20,by0-60,W-20,by1),radius=60,fill=255); db.rectangle((0,0,W,by0-1),fill=0)
    metal=lin((W,H),[(0,(96,96,102)),(0.012,(236,236,240)),(0.03,(138,138,145)),(0.06,(112,112,118)),(0.5,(134,134,141)),(0.94,(112,112,118)),(0.97,(138,138,145)),(0.988,(236,236,240)),(1,(96,96,102))],0)
    put(out,metal,base)
    shade=lin((W,H),[(0,(0,0,0)),(1,(0,0,0))],90).convert('RGBA'); a=np.zeros((H,W)); yy=np.arange(H)[:,None]; a+=np.clip((yy-by0)/(by1-by0),0,1)**1.5*178; sm=Image.fromarray(a.astype('uint8'),'L'); shade.putalpha(ImageChops.multiply(sm,base)); out.alpha_composite(shade)
    over(out,(210,210,218),ImageChops.multiply(base,rr((W,H),(20,by0,W-20,by0+3),0)).point(lambda v:int(v*0.6)))
    lip=rr((W,H),(W//2-215,by0-40,W//2+215,by0+27),24); lm=ImageChops.multiply(lip,base); put(out,lin((W,H),[(0,(58,58,62)),(0.5,(172,172,179)),(1,(58,58,62))],0),lm)
    over(out,(0,0,0),ImageChops.multiply(rr((W,H),(W//2-215,by0,W//2+215,by0+6),0),base).point(lambda v:int(v*0.5)))
    out=out.crop((0,0,W,by1+8)); out=out.resize((width,int(out.size[1]*width/W)),Image.LANCZOS); out.save(dst); print(dst.split('/')[-1],out.size)


def main():
    global F
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for name in ("fonts", "desktop", "phone", "token"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--out", default=".")
    args = parser.parse_args()
    F = args.fonts.rstrip("/") + "/"
    out = pathlib.Path(args.out)
    laptop(args.desktop, str(out / "app-desktop.png"), 2240)
    phone(args.phone, str(out / "app-phone.png"), 660)
    phone(args.token, str(out / "app-0zkusdc.png"), 760)


if __name__ == "__main__":
    main()
