"""Inspect the compact PSU bracket: rear outlines, shelf feet and print orientation."""
from pathlib import Path
import cadquery as cq
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def render(out: Path):
    fig=plt.figure(figsize=(15,5.6))
    name,width='psu_bracket',92.5
    shape=cq.importers.importStep(str(out/f'{name}.step'))
    vertices,triangles=shape.val().tessellate(.15)
    pts=np.array([v.toTuple() for v in vertices]);faces=pts[np.array(triangles)]
    color='#36a1a1'
    ax=fig.add_subplot(1,3,1)
    ax.add_collection(PolyCollection(faces[:,:,:2],facecolors=color,edgecolors='none'))
    ax.add_patch(Rectangle((0,0),86,150,fill=False,ec='#333333',ls='--',lw=1.3))
    ax.set(xlim=(-4,97),ylim=(154,-4),aspect='equal',xlabel='Width (mm)',ylabel='Down from PSU top (mm)',title='Rear outline')
    ax.add_patch(Rectangle((16,10),54,41,fill=False,ec='#bc4d39',ls=':',lw=1.3))
    ax.text(43,65,'8 mm top bar\n≥2 mm edge clearance',ha='center',fontsize=9)
    ax.text(43,90,'9 × 40 mm\nLED relief →',ha='center',fontsize=10)
    ax=fig.add_subplot(1,3,2)
    ax.add_collection(PolyCollection(faces[:,:,[0,2]],facecolors=color,edgecolors='none'))
    ax.scatter([31,55],[19,19],s=15,color='white')
    ax.set(xlim=(-4,97),ylim=(35,-5),aspect='equal',xlabel='Width (mm)',ylabel='Behind PSU (mm)',title='Top: 50 × 30 mm shelf foot')
    ax.text(43,33,'Slots: X31 / X55, depth19 mm',ha='center',fontsize=10)
    ax=fig.add_subplot(1,3,3,projection='3d')
    normals=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-9)
    colors=np.array([.22,.63,.63])[None,:]*(.55+.4*np.abs(normals@[.3,-.4,.866])[:,None])
    ax.add_collection3d(Poly3DCollection(faces,facecolors=colors,edgecolors=colors,linewidths=.05))
    ax.set(xlim=(0,width),ylim=(0,150),zlim=(0,30));ax.set_box_aspect((width,150,30));ax.view_init(38,-55);ax.set_axis_off();ax.set_title('Print broad rear face down')
    fig.suptitle('Compact PSU bracket • 0.4 mm hardened steel nozzle • HT-PLA-GF',fontsize=18)
    fig.text(.5,.035,'Dashed outline: 86 × 150 mm PSU rear face. Only the LED bypass extends 6.5 mm sideways.\nFeet project 30 mm behind the PSU; two slotted shelf anchors per bracket. Anneal, then verify holes and plug clearance.',ha='center',fontsize=11)
    fig.subplots_adjust(top=.84,bottom=.2,wspace=.4)
    fig.savefig(out/'psu-bracket.png',dpi=150);plt.close(fig)


if __name__=='__main__':render(Path(__file__).resolve().parents[1]/'models')
