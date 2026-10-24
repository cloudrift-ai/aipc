"""Section diagram of a metal GPU base passing through the printed adapter."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
import pcie_post_hardware as hw


def render(out):
    stack = hw.thread_stack(1.2)
    fig, ax = plt.subplots(figsize=(11, 6))
    half_width = hw.OPENING_WIDTH/2
    body_width = hw.BASE_AF
    layers = [(-22,-1.2,44,1.2,'#89949d'),
              (-18,0,18-half_width,6,'#59b4bd'), (half_width,0,18-half_width,6,'#59b4bd'),
              (-body_width/2,0,body_width,hw.BASE_HEIGHT,'#ceb76d'),
              (-6,-2.2,12,1,'#b8bfc6'), (-3.5,-2.7,7,.5,'#b8bfc6')]
    for x,y,w,h,c in layers:
        ax.add_patch(Rectangle((x,y),w,h,facecolor=c,edgecolor='#39424a',lw=.7))
    ax.add_patch(Rectangle((-1.5,-2.7),3,hw.BASE_HEIGHT+2.7,facecolor='white'))
    ax.add_patch(Rectangle((-1.5,-2.7),3,hw.BOTTOM_SCREW_LENGTH,facecolor='#646f7a'))
    ax.add_patch(Rectangle((-2.75,-5.7),5.5,3,facecolor='#646f7a',edgecolor='#39424a'))
    ax.add_patch(Rectangle((-1.5,hw.BASE_HEIGHT-hw.OBT_STUD_LENGTH),3,hw.OBT_STUD_LENGTH,facecolor='#777e86'))
    ax.add_patch(Rectangle((-3,hw.BASE_HEIGHT),6,9,facecolor='#777e86',edgecolor='#39424a'))
    ax.plot([0,0],[-7,25],ls='-.',lw=.6,color='#976846')
    labels = [(0,21,27,24,'OBT rod: 9 mm male thread\nOwner-reported; fixed nut height needs dry-fit'),
              (2.75,10,27,18,'Würth 970140324: 14 mm base\nM3 through-thread, SW5.5 hex'),
              (11,3,27,11,f'Regular hex hole: {hw.OPENING_AF:g} mm across flats\n{hw.BODY_FACE_CLEARANCE:g} mm per face; snug fit, fixed centre'),
              (0,4.15,27,5,f"{stack['nominal_tip_clearance_mm']:.1f} mm nominal gap between screw tips"),
              (19,-.6,27,-1,'Base seats directly on solid shelf steel\nØ3.5 mm drilled hole; no upper washer'),
              (5,-1.7,27,-7,'Below steel: Ø12 × 1 + Ø7 × 0.5 washers'),
              (0,-4.5,-34,-10,'M3 × 6 screw from below\n3.3 mm nominal engagement')]
    for x,y,tx,ty,label in labels:
        ax.annotate(label,(x,y),xytext=(tx,ty),fontsize=10,va='center',ha='left',
                    arrowprops={'arrowstyle':'-','lw':.8,'color':'#5c6975'})
    ax.set(xlim=(-36,109),ylim=(-14,28)); ax.set_aspect('equal'); ax.axis('off')
    fig.suptitle('GPU post mounts directly to steel through the plastic adapter',fontsize=16,y=.97)
    plan = fig.add_axes([.045,.62,.16,.24])
    plan.add_patch(Polygon(hw.opening_points(),facecolor='white',edgecolor='#39939e',lw=2))
    plan.add_patch(Polygon(hw.base_hex_points(),facecolor='#ceb76d',edgecolor='#75602f'))
    plan.set(xlim=(-4,4),ylim=(-4.5,4.5),aspect='equal')
    plan.axis('off')
    plan.set_title('Top view: true hex\nCorner toward PCB',fontsize=9)
    plan.annotate('PCB direction',(0,-4.2),ha='center',fontsize=8,color='#bb2639')
    fig.text(.06,.06,'Nominal stack uses 1.2 mm shelf steel. Rod seat Z14 is 2.5 mm lower than the previous mount.\nCheck the fixed lower OBT nut against a fully seated card; do not use the retaining nut to pull the card into position.',fontsize=10)
    fig.subplots_adjust(left=.03,right=.98,top=.9,bottom=.18)
    fig.savefig(Path(out)/'pcie-post-shared-mount.png',dpi=170)
    plt.close(fig)


if __name__=='__main__':
    render(Path(__file__).resolve().parents[1]/'models')
