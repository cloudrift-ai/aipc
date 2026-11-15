# GPU lab: a test rig for mixed GPUs

**Status: planning.** Nothing here is selected, bought, modeled or measured yet. This page records the intended design and the open questions.

## Goal

Test about 16 different GPUs (datacenter and consumer, NVIDIA and others) with each card isolated, so that:

- every GPU can run its own driver branch (for example, Volta is not supported after NVIDIA's R580 branch, while new cards need current drivers);
- a hung or faulty card under test affects only its own tests;
- cards can be swapped often without disturbing the others.

## Intended design

**Nodes.** Two or more single-socket EPYC hosts with about 8 GPUs each, instead of one 16-GPU host. That leaves lanes for the NIC and storage, splits the power and limits the damage from one bad card.

**One VM per GPU.** Each GPU is passed through to its own VM (VFIO), managed with CloudRift: lab nodes run as CloudRift provider nodes in a private cluster or team, and each test rents a one-GPU VM, runs the suite and releases it. Requirements: each GPU in its own IOMMU group, and cards that reset cleanly between VMs.

**PCIe link per GPU: x8 over a cable.**

```
CPU ── x16 slot (BIOS: x8x8) ── host adapter: x16 → 2 × MCIO 8i
                                    │
                              MCIO 8i cable (Gen4, ≤ ~0.5–0.75 m)
                                    │
                         device board: MCIO 8i → x16 slot (x8 electrical) + 6/8-pin power
                                    │
                                   GPU
```

- Passive host adapters need x8x8 bifurcation in BIOS. Without it, use a PCIe switch card (shared uplink).
- Boards with native MCIO ports (for example Gigabyte MZ33-AR1) need no host adapter.
- Lock the links to Gen4 for cable margin. x8 Gen4 is about 16 GB/s, so host-to-device bandwidth results reflect the link.
- Buy the host adapter, cables and device boards as a matched set. Check per-port REFCLK/PERST#, lane order (0–7) and that the slot power comes from the same PSU as the GPU.

**Mechanics: cards upright in a row on T-slot extrusion.**

- Bracket rail: each GPU bracket screws to a T-nut, so the card spacing adjusts to each card's width.
- Riser rail below it: each MCIO device board sits on a carrier that places its slot where a motherboard slot would be relative to the bracket (PCIe CEM: bracket outside face 59.05 mm behind the connector key; see [aipc/docs/design.md](../aipc/docs/design.md)).
- Tail rail: an adjustable post with a silicone pad under the far end of every card. Heavy consumer cards (an RTX 5090 is about 2.2 kg) must not hang on the riser connector.
- Spacing for open-air coolers: card thickness plus about 15–25 mm (about 85–95 mm for a 5090-class card). Eight such cards need about 720 mm, so run the row front to back or use two rows of four.
- Front-to-back airflow with a fan wall or duct. Keep one card's exhaust out of the next card's intake.
- A fixed-pitch backplane (for example an ADT-Link 11-slot board on 40 mm pitch) suits a node of 2-slot datacenter cards only.

**Power.** Plan about 300 W per GPU on average and 575 W for 5090-class cards. Each 8-GPU node needs several PSUs that power on together with a common ground, on 240 V circuits.

## Candidate boards (unverified)

| Board | Lanes exposed | GPUs at x8 | Notes |
| --- | --- | --- | --- |
| Gigabyte MZ33-AR1 (SP5) | 4 × x16 + 6 × MCIO 8i | up to 14 | Native MCIO; needs qualified cables for Gen5 |
| ASRock Rack GENOAD8X-2T/BCM (SP5) | 7 × x16 + 1 × x8 | up to 14 | Slot bifurcation not confirmed; some slots share lanes |
| ASRock Rack ROMED8-2T (SP3) | 7 × x16 | about 14 | Gen4; cheaper platform |
| HUANANZHI H12D-8D (SP3, Berserk's board) | 4 × x16 + 3 × SFF-8643 x4 | 8 | Only with x8x8 bifurcation; its manual does not mention it |

## Open questions

1. Which GPUs will be tested? This sets the node grouping, power and card spacing.
2. Does the H12D-8D BIOS offer x8x8 bifurcation? Check in Berserk's BIOS.
3. Which host adapter, cable and device board set, and does it give each port its own REFCLK?
4. Can CloudRift run lab nodes in a private cluster, and how are nodes onboarded?
5. Power circuits and cooling capacity available in the lab room.

## Test suite (draft)

Per GPU at first boot and after every swap: `lspci -vv` link speed and width, AER counters at zero under load, `nvidia-smi` / DCGM diagnostics, `gpu-burn`, `nvbandwidth`, and the equivalent ROCm tools for AMD cards. Log Xid and AER events per slot.
