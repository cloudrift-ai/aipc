"""Selected H12D-8D/7702P replacement; photographic placement is provisional.

Photo is unmodified Huananzhi 1741911996630761326.png. PCB bounds are
(209,19)..(1372,1477) pixels. Rotation maps image bottom to shelf low X,
image left (rear I/O) to shelf high Y. Never use these estimates to drill.
"""
MODEL = 'HUANANZHI H12D-8D + BMC'
CPU = 'AMD EPYC 7702P'
WIDTH, DEPTH = 305.0, 245.0
X, REAR_Y = 137.0, 314.2
FRONT_Y = REAR_Y - DEPTH
CPU_CORES, CPU_THREADS, CPU_TDP_W = 64, 128, 200
RAM = '128 GB: 8 x 16 GB DDR4-3200 ECC RDIMM; exact modules unselected'
LISTING = 'https://www.ebay.com/itm/396800856844'
SOURCE = 'https://www.huananzhi.com/en/list_6/177.html'
PHOTO = 'manufacturer board image 1741911996630761326.png from ' + SOURCE
POPULATED_SITES = ('A','C','F','G','H','K','L','M')

def photo_xy(px, py):
    return X + (1477-py)*WIDTH/1458, REAR_Y-(px-209)*DEPTH/1163

# First slot is photograph-derived; remaining slots use nominal two-slot pitch.
# These are PCB planes, NOT the low-X faces of the dual-slot cooler envelopes.
SLOT_PLANES = {f'PCIE{i+1}': round(279.50-i*40.64,2) for i in range(4)}
GPU_BODY_X = {k: round(v-36.0,2) for k,v in SLOT_PLANES.items()}
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
