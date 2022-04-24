import subprocess


def generate_scad_preview(scad_path: str, preview_output_path: str):
    subprocess.run(
        [
            "openscad",
            "--camera=0,0,5,0,0,0,200",
            "--projection=o",
            "--colorscheme=Tomorrow Night",
            "-o",
            preview_output_path,
            scad_path,
        ],
        check=True,
        capture_output=True,
    )


def generate_scad_render(scad_path: str, render_output_path: str):
    subprocess.run(
        [
            "openscad",
            "-o",
            render_output_path,
            scad_path,
        ],
        check=True,
        capture_output=True,
    )
