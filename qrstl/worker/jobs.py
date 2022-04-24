import qrstl.worker.scad as scad

from qrstl.qr import QrCodeParams, generate_qr_scad


def generate_scad_code(params: QrCodeParams):
    generate_qr_scad(params, f"qrout/{params.sha}.scad")


def generate_scad_preview(params: QrCodeParams):
    scad.generate_scad_preview(f"qrout/{params.sha}.scad", f"qrout/{params.sha}.png")


def generate_scad_render(params: QrCodeParams):
    scad.generate_scad_render(f"qrout/{params.sha}.scad", f"qrout/{params.sha}.stl")
