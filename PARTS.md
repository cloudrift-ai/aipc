# Parts list

Everything needed to build both PCs on the open shelf: the shared shelf and mounting hardware, then each PC's components. Prices are USD before tax and shipping, as listed in October 2026; a blank price means it was not quoted. Printed parts are in [print/](print/README.md).

## Shelf and mounting hardware

| Item | Qty | Unit price | Link | Notes |
| --- | ---: | ---: | --- | --- |
| StarTech ADJSHELFHDV 1U four-post vented shelf | 1 | $166.13 | [DigiKey](https://www.digikey.com/en/products/detail/startech-com/ADJSHELFHDV/22260579) | 700 × 446 mm steel deck. The build drills new mounting holes into it; survey the real lips, vents and cabinet liners first. |
| Keystone 1451B #6-32 F/F brass standoff, 3/8 in (9.53 mm) | 17 | $0.88 | [DigiKey](https://www.digikey.com/en/products/detail/keystone-electronics/1451B/303586) | Eight for the H12D, nine for the X870E. Fit only the board's populated holes; ground one standoff to the shelf. |
| Open Benchtable PCI-E support + nut, 2-pack | 5 | $10.00 | [Open Benchtable](https://store.openbenchtable.com/products/obt-pci-e-thumbscrew-nut-pack) | Ten metal posts, two per GPU, for five GPUs. |
| Würth 970100354 M3 F/F brass standoff, 10 mm | 10 | $0.47 | [DigiKey](https://www.digikey.com/en/products/detail/w%C3%BCrth-elektronik/970100354/9488551) | One under each GPU post; clamps the post and the motherboard adapter to the steel. |
| Shelf fasteners and backing washers | 39 joints | | | 25 M4 joints (21 printed mounts, four V100 tail spacers) and 14 M3 joints (four front motherboard anchors, ten GPU-post joints). Stacks and lengths are in [mount-hole-manifest.json](models/mount-hole-manifest.json) and the [assembly guide](docs/assembly.md#fasteners-and-access). |
| Component fasteners and interface hardware | 1 set | | | 17 low-head #6-32 standoff screws, PSU and radiator screws, four M4 × 20 mm F/F metal tail spacers with 4 mm silicone pads, nonconductive foam seal for the GPU hood. |
| AC power cords | 2 | | | Corsair: low-profile or down-exit C13. Rosewill: match its inlet and the UPS outlet (it may need C19). |
| Printed parts | 18 | | [print/](print/README.md) | 17 installed parts plus one fit coupon, on 14 plates. |

## Berserk: EPYC with four V100s

| Item | Qty | Unit price | Link | Notes |
| --- | ---: | ---: | --- | --- |
| HUANANZHI H12D-8D + BMC with AMD EPYC 7702P (64 cores) | 1 | $1,250.00 | [eBay listing](https://www.ebay.com/itm/396800856844), [maker](https://www.huananzhi.com/en/list_6/177.html) | 305 × 245 mm SP3 board, four PCIe 4.0 x16 slots, eight memory channels. Confirm PCB revision, CPU marking and that the CPU is not vendor-locked. |
| DDR4-3200 ECC RDIMM, 16 GB | 8 | | | One per channel, 128 GB total. Buy a matched set supported by the board. |
| NVIDIA Tesla V100 PCIe 16 GB | 4 | $244.99–359.99 | [eBay](https://www.ebay.com/itm/327314931099), [eBay](https://www.ebay.com/itm/127840399241), [product brief](https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/tesla-product-literature/Tesla-V100-PCIe-Product-Brief.pdf) | Genuine PCIe cards, passive 250 W. Remove the OEM extenders. Start around 180 W per card. |
| V100 power adapter, dual PCIe 8-pin to CPU/EPS 8-pin (030-0571-000 compatible) | 4 | $20.90 | [eBay](https://www.ebay.com/itm/256383020187) | Check the pinout against NVIDIA's brief before use. Never plug a PCIe 8-pin straight into a V100. |
| Low-profile 90° CPU/EPS 8-pin extension | 4 | $14.99 | [MODDIY](https://www.moddiy.com/products/5840/CPU-EPS-90%C2%B0-L-Shape-Mini-Low-Profile-EPS-Power-Cable-8-Pin-Down-Angle.html) | Keeps the GPU power leads under the 6U ceiling. The CAD reserves 18 mm; verify the real projection and rating. |
| Sanyo Denki 9GV1412P1S001 fan, 140 × 140 × 38 mm | 1 | $82.26 | [DigiKey](https://www.digikey.com/en/products/detail/sanyo-denki-america-inc/9GV1412P1S001/8284659) | Pulls air through all four V100 heatsinks via the printed hood. 12 V, 3.1 A. |
| PSU-powered fan controller and harness | 1 | | [fan catalog](https://publish.sanyodenki.com/San_Ace_E/book/data/San_Ace_E.pdf) | 12 V motor power from the PSU (not a motherboard header), 25 kHz PWM, tach monitoring, control from the hottest GPU. |
| GPU fan and exhaust fasteners | 1 set | | [T-nut example](https://www.amazon.ae/Sutemribor-Hammer-Fastener-Aluminum-Profile/dp/B07FPLZXTF) | 8 M4 2020 hammer T-nuts, 4 M4 × 14 and 4 M4 × 16 socket-cap screws, 8 OD9 × 1 washers; roof: 4 M4 × 20 bolts, 4 nuts, 8 OD12 × 1 washers. |
| McMaster 53185K52 lever-release hose clamp | 2 | $21.92 | [McMaster](https://www.mcmaster.com/53185K52/) | One at each end of the duct. |
| 6-inch wire-supported flexible duct | 1 m | | | Uninsulated; trim after fitting. |
| 2 mm silicone foam gasket sheet, 200 × 200 mm | 1 | | | Roof-flange seal. |
| Samsung 960 PRO 1 TB NVMe | 2 | | | Reused. |
| Corsair Hydro H115i (280 mm AIO) | 1 | | | Reused. Needs a compatible SP3 mounting bracket; check cold-plate coverage and hose reach. |
| Rosewill Hercules 1600 W PSU | 1 | | | Reused, with its own modular cables. Needs 24-pin, two EPS 8-pin and eight PCIe 8-pin feeds. |

## Kenshin: Ryzen with an RTX 5090

| Item | Qty | Unit price | Link | Notes |
| --- | ---: | ---: | --- | --- |
| AMD Ryzen 9 9950X3D | 1 | | | |
| Gigabyte X870E AORUS PRO (ATX) | 1 | | | |
| Corsair CMP64GX5M4B6400C32 DDR5 kit, 4 × 16 GB | 1 | | | |
| Zotac Gaming GeForce RTX 5090 Solid 32 GB | 1 | | | |
| Samsung 990 PRO 4 TB NVMe | 2 | | | |
| Corsair HX1200i PSU | 1 | | | |
| Lian Li GA II LITE Performance 360 (GA2L36PB) | 1 | | [specs](https://lian-li.com/product/ga-ii-lite/) | 360 mm AIO with three 120 mm fans; mounted at the shelf rear, exhausting rearward. |
