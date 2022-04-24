import pathlib

from fastapi import FastAPI
from pydantic import BaseModel

from qrstl.qr import QrCodeParams
from qrstl.worker.api import enqueue_preview_job

app = FastAPI()


class QrCodeApiParams(BaseModel):
    data: str

    title: str | None = None
    title_font: str = "Liberation Mono:style=Bold"
    title_size_mm: float = 8

    subtitle: str | None = None
    subtitle_font: str = "Liberation Mono:style=Italic"
    subtitle_size_mm: float = 6

    titles_spacing_mm: float = 3
    titles_thickness_mm: float = 0.4

    qr_size_mm: float = 50
    qr_border_mm: float = 5
    qr_thickness_mm: float = 0.6

    frame_thickness_mm: float = 1
    frame_outline_mm: float = 1
    frame_outline_thickness_mm: float = 0.2
    frame_fillet_radius_mm: float = 5

    nfc: bool = True
    nfc_diameter_mm: float = 30
    nfc_thickness_mm: float = 0.2
    nfc_base_offset_mm: float = 0.2

    magnets: bool = True
    magnets_diameter_mm: float = 5.5
    magnets_thickness_mm: float = 1.2
    magnets_inset_mm: float = 2

    def to_qr_code_params(self) -> QrCodeParams:
        return QrCodeParams(
            data=self.data,
            title=self.title,
            title_font=self.title_font,
            title_size_mm=self.title_size_mm,
            subtitle=self.subtitle,
            subtitle_font=self.subtitle_font,
            subtitle_size_mm=self.subtitle_size_mm,
            titles_spacing_mm=self.titles_spacing_mm,
            titles_thickness_mm=self.titles_thickness_mm,
            qr_size_mm=self.qr_size_mm,
            qr_border_mm=self.qr_border_mm,
            qr_thickness_mm=self.qr_thickness_mm,
            frame_thickness_mm=self.frame_thickness_mm,
            frame_outline_mm=self.frame_outline_mm,
            frame_outline_thickness_mm=self.frame_outline_thickness_mm,
            frame_fillet_radius_mm=self.frame_fillet_radius_mm,
            nfc=self.nfc,
            nfc_diameter_mm=self.nfc_diameter_mm,
            nfc_thickness_mm=self.nfc_thickness_mm,
            nfc_base_offset_mm=self.nfc_base_offset_mm,
            magnets=self.magnets,
            magnets_diameter_mm=self.magnets_diameter_mm,
            magnets_thickness_mm=self.magnets_thickness_mm,
            magnets_inset_mm=self.magnets_inset_mm,
        )


@app.post("/preview")
def preview_post(params: QrCodeApiParams):
    qr_params = params.to_qr_code_params()

    enqueue_preview_job(qr_params)

    return {"id": qr_params.sha}


@app.get("/preview/{job_id}")
def preview_get(job_id: str):
    path = pathlib.Path(f"qrout/{job_id}.png")
    if not path.exists():
        return {"error": "Not found"}
    else:
        return path.read_bytes()
