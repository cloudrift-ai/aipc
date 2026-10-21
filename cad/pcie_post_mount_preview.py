"""Section diagram of the shared GPU-post / motherboard-adapter shelf joint."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def render(out):
    fig,ax=plt.subplots(figsize=(10,6))
    layers=[(-22,-1.2,44,1.2,'#89949d','Steel shelf · 1.2 mm nominal'),
            (-18,0,36,6,'#59b4bd','Motherboard adapter · 6 mm'),
            (-4.5,6,9,.5,'#b8bfc6','Top steel washer · Ø9 × 0.5 mm'),
            (-2.89,6.5,5.78,10,'#ceb76d','M3 female/female base · 10 mm'),
            (-6,-2.2,12,1,'#b8bfc6','Steel backing washer · Ø12 × 1 mm'),
            (-3.5,-2.7,7,.5,'#b8bfc6','Small M3 washer · Ø7 × 0.5 mm')]
    for x,y,w,h,c,_ in layers:
        ax.add_patch(Rectangle((x,y),w,h,facecolor=c,edgecolor='#39424a',lw=.7))
    ax.add_patch(Rectangle((-2.75,0),5.5,6,facecolor='white',edgecolor='none'))
    ax.add_patch(Rectangle((-1.5,-2.7),3,12,facecolor='#646f7a',edgecolor='#39424a'))
    ax.add_patch(Rectangle((-2.75,-5.7),5.5,3,facecolor='#646f7a',edgecolor='#39424a'))
    ax.add_patch(Rectangle((-1.5,12.5),3,12,facecolor='#777e86',edgecolor='#39424a'))
    ax.plot([0,0],[-7,27],ls='-.',lw=.7,color='#976846')
    labels=[(0,23,28,25,'OBT GPU support rod\nMale M3 end; verify actual stud length'),
            (2.9,11.5,28,19,'Existing threaded base\nHold SW5 flats while tightening'),
            (4.5,6.3,28,13,'Ø9 × 0.5 mm steel washer'),
            (13,3,28,7,'6 mm printed adapter\n10 × 5.5 mm adjustment slot'),
            (18,-.6,28,1,'Shelf steel · drill Ø3.5 mm\nSlot transfers position; it is not a drill bushing'),
            (5,-1.7,28,-5,'Ø12 backing + Ø7 small washer'),
            (0,-4.5,-33,-8,'M3 × 12 screw from below\n2.8 mm nominal engagement in base')]
    for x,y,tx,ty,label in labels:
        ax.annotate(label,(x,y),xytext=(tx,ty),fontsize=10,va='center',ha='left',arrowprops={'arrowstyle':'-','lw':.8,'color':'#5c6975'})
    ax.set(xlim=(-36,96),ylim=(-12,29));ax.set_aspect('equal');ax.axis('off')
    fig.suptitle('One joint secures the GPU post and motherboard adapter',fontsize=16,y=.97)
    fig.text(.06,.07,'Eight selectable slots per motherboard. Populate only the positions required by the seated cards.\nConfirm both thread engagements, no internal bottoming, and top-nut adjustment with the GPU fully seated.',fontsize=10)
    fig.subplots_adjust(left=.03,right=.98,top=.9,bottom=.18)
    fig.savefig(Path(out)/'pcie-post-shared-mount.png',dpi=170)
    plt.close(fig)


if __name__=='__main__':
    render(Path(__file__).resolve().parents[1]/'models')
