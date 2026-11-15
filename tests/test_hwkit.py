import json
import zipfile

from hwkit import compat, paths, plates, printers, slicer, spec


def test_build_root_comes_from_build_toml():
    assert (paths.ROOT / "build.toml").is_file()
    assert paths.ROOT.name == "aipc"
    assert paths.ASSEMBLY_STEP.is_file()


def test_every_part_spec_lints_clean():
    assert spec.lint(spec.load_all()) == []


def test_no_compatibility_failures():
    assert [c for c in compat.run_checks() if c["status"] == "FAIL"] == []


def test_printer_presets_flatten_and_match_policy():
    printer = printers.get()
    bases = slicer.base_presets()
    machine = slicer.flatten(json.loads(printer.machine_preset.read_text()), bases)
    assert machine["nozzle_diameter"] == [f"{printer.config['nozzle_mm']:g}"]
    process = slicer.flatten(printer.load_profile("printer:process.json"), bases)
    for key, value in printer.config["gcode"]["settings"].items():
        if key in process:
            current = process[key][0] if isinstance(process[key], list) else process[key]
            assert current == value, key


def test_plate_manifest_profiles_exist_and_have_materials():
    printer = printers.get()
    jobs = json.loads((paths.PRINT / "manifest.json").read_text())["jobs"]
    for job in jobs.values():
        assert printer.profile(job["process_profile"]).is_file()
        filament = printer.profile(job["filament_profile"])
        assert filament.is_file()
        assert filament.name in printer.materials


def test_plates_center_and_write_3mf(tmp_path):
    cube = (
        [(0, 0, 0), (10, 0, 0), (10, 20, 0), (0, 20, 0), (0, 0, 5)],
        [(0, 1, 2), (0, 2, 3), (0, 1, 4)],
        (10.0, 20.0, 5.0),
    )
    placed = plates.center_group([("cube", 0, 0)], {"cube": cube}, (270.0, 200.0))
    assert placed == [("cube", 130.0, 90.0)]
    out = tmp_path / "plate.3mf"
    plates.make_3mf(out, placed, {"cube": cube})
    with zipfile.ZipFile(out) as z:
        model = z.read("3D/3dmodel.model").decode()
    assert 'name="cube"' in model and "1 0 0 0 1 0 0 0 1 130.0 90.0 0" in model
