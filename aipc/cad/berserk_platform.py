"""Selected H12D-8D/7702P replacement; photographic placement is provisional.

Photo is unmodified Huananzhi 1741911996630761326.png. PCB bounds are
(209,19)..(1372,1477) pixels. Rotation maps image bottom to shelf low X,
image left (rear I/O) to shelf high Y. Never use these estimates to drill.
"""
from rack_shelf_coordinates import BERSERK_DX, BERSERK_DY

MODEL = 'HUANANZHI H12D-8D + BMC'
CPU = 'AMD EPYC 7702P'
from hwkit import spec

WIDTH, DEPTH = spec.dim('huananzhi-h12d-8d', 'pcb_width'), spec.dim('huananzhi-h12d-8d', 'pcb_depth')
X, REAR_Y = 137.0+BERSERK_DX, 314.2+BERSERK_DY
FRONT_Y = REAR_Y - DEPTH
CPU_CORES, CPU_THREADS, CPU_TDP_W = 64, 128, 200
RAM = '256 GB: 8 x 32 GB Micron DDR4-2933 ECC RDIMM ordered; receipt/testing pending'
LISTING = 'https://www.ebay.com/itm/396800856844'
SOURCE = 'https://www.huananzhi.com/en/list_6/177.html'
PHOTO = 'manufacturer board image 1741911996630761326.png from ' + SOURCE
POPULATED_SITES = ('A','C','F','G','H','K','L','M')

def photo_xy(px, py):
    return X + (1477-py)*WIDTH/1458, REAR_Y-(px-209)*DEPTH/1163

# PCIe connector centrelines (= card PCB planes), NOT the low-X faces of the
# dual-slot cooler envelopes. PCIe CEM 2.0 Fig. 6-14 puts the slot nearest the
# I/O 47.29 mm from the microATX datum, which is ATX hole B at 3.75 in from the
# board's low-X edge; slots step 20.32 mm (ATX 2.2 Fig. 3). The H12D x16 slots
# take every second position. The earlier photo estimate agreed within 0.04 mm.
SLOT_PITCH = 20.32
ATX_HOLE_B_X = 3.75*25.4
PCIE_SLOT1_FROM_HOLE_B = 47.29
SLOT_PLANES = {f'PCIE{i+1}': round(X+ATX_HOLE_B_X+PCIE_SLOT1_FROM_HOLE_B-2*i*SLOT_PITCH,2) for i in range(4)}
GPU_BODY_X = {k: round(v-36.0,2) for k,v in SLOT_PLANES.items()}
# OBT rod axes = bracket screw notches. CEM Fig. 6-5 puts the notch on the PCB
# plane (1.27 mm ref); a dual-slot bracket's second tab is one slot pitch
# toward the cooler (low X). Earlier body+7/+27 guesses sat about 9 mm toward
# the cooler, which a seated-card photo (2026-11-14) showed as leaning rods.
BRACKET_POST_X = {k: (round(v,2), round(v-SLOT_PITCH,2)) for k,v in SLOT_PLANES.items()}
GPU_WIDTH = 40.0  # provisional 36 mm component side / 4 mm back side
GPU_CENTER = (min(GPU_BODY_X.values())+max(GPU_BODY_X.values())+GPU_WIDTH)/2
CPU_CENTER = photo_xy(833,397)
M2_STANDOFFS = [photo_xy(430,y) for y in (892,1088,1284)]
EPS_PROJECTION = 18.0  # target allowance for angled EPS, NOT a product dimension

def report():
    return {'date':'2026-10-20','motherboard':MODEL,'cpu':CPU,
        'cores':CPU_CORES,'threads':CPU_THREADS,'cpu_TDP_W':CPU_TDP_W,
        'memory':RAM,'PCB_mm':[WIDTH,DEPTH],'listing':LISTING,'source':SOURCE,
        'PCB_revision':'seller confirmation required; V1 photo/manual used for placement',
        'purchase_status':'Unordered; user selected, no order/receipt evidence',
        'installed':False,'BMC':'included per listing; remote console/media not tested',
        'slot_PCB_planes_x_mm':SLOT_PLANES,'GPU_body_low_x_mm':GPU_BODY_X,
        'GPU_body_offset_basis':'provisional 36 mm toward low X, 4 mm toward high X; measure real PCIe card',
        'slot_lane_widths':{k:16 for k in SLOT_PLANES},'V100_link':'PCIe 3.0 x16 each',
        'populated_ATX_sites':POPULATED_SITES,'absent_ATX_sites':['B','J'],
        'hole_basis':'ATX 2.01 datums; eight sites visible in manufacturer photograph; delivered PCB unmeasured',
        'placement_basis':PHOTO+'; photo estimates, not manufacturer CAD',
        'CPU_center_xy_mm':CPU_CENTER,'M2_2280_standoffs_xy_mm':M2_STANDOFFS,
        'angled_EPS_projection_target_mm':EPS_PROJECTION,
        'angled_EPS_status':'candidate only; verify pinout, current rating, exit direction and installed projection',
        'physical_fit_verified':False}
