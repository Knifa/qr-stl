import hashlib
from dataclasses import dataclass, field
from typing import List

import qrcode
import solid as so
import solid.utils as su

QrCodeData = List[List[str]]

FRAME_COLOR = [x / 255 for x in [0x2D, 0x31, 0x42]]
QR_COLOR = [x / 255 for x in [0xEF, 0x83, 0x64]]
TITLE_COLOR = [x / 255 for x in [0xFF, 0xFF, 0xFF]]
OUTLINE_COLOR = [x / 255 for x in [0xBF, 0xC0, 0xC0]]

ROUND_SEGMENTS = 32
CORNER_ITER = ((1, 1), (-1, 1), (-1, -1), (1, -1))
TITLE_KERNING = 1


@dataclass
class QrCodeParams:
    data: str

    title: str | None = None
    title_font: str = "Liberation Mono:style=Bold"
    title_size_mm: float = 10

    subtitle: str | None = None
    subtitle_font: str = "Liberation Mono:style=Italic"
    subtitle_size_mm: float = 8

    titles_spacing_mm: float = 3
    titles_thickness_mm: float = 0.6

    qr_size_mm: float = 50
    qr_border_mm: float = 2.5
    qr_thickness_mm: float = 0.6

    frame_thickness_mm: float = 2
    frame_outline_mm: float = 0
    frame_outline_thickness_mm: float = 0.6
    frame_fillet_radius_mm: float = 5

    nfc: bool = True
    nfc_diameter_mm: float = 30
    nfc_thickness_mm: float = 0.6
    nfc_base_offset_mm: float = 0.6

    magnets: bool = True
    magnets_diameter_mm: float = 5.5
    magnets_thickness_mm: float = 1.2
    magnets_inset_mm: float = 2

    @property
    def sha(self):
        return hashlib.sha256(repr(self).encode("utf-8")).hexdigest()


@dataclass
class QrCodeParamsCalculated(QrCodeParams):
    qr_data: QrCodeData = field(init=False)
    frame_bottom_spacing_mm: float = field(init=False)
    frame_width_mm: float = field(init=False)
    frame_length_mm: float = field(init=False)

    def __post_init__(self):
        self.frame_width_mm = (
            self.qr_size_mm + (self.qr_border_mm + self.frame_outline_mm) * 2
        )

        if self.title is not None and self.subtitle is not None:
            self.frame_bottom_spacing_mm = (
                self.title_size_mm
                + self.subtitle_size_mm
                + self.titles_spacing_mm
                + self.qr_border_mm
            )
        elif self.title is not None:
            self.frame_bottom_spacing_mm = self.title_size_mm + self.qr_border_mm
        else:
            self.frame_bottom_spacing_mm = 0

        if self.title:
            titles_width = self.title_size_mm * TITLE_KERNING * len(self.title)

            if self.subtitle:
                titles_width = max(
                    titles_width,
                    self.subtitle_size_mm * TITLE_KERNING * len(self.subtitle),
                )

            total_width = self.frame_width_mm + self.qr_border_mm * 2
            self.frame_bottom_spacing_mm *= min(total_width / titles_width, 1)

        self.frame_length_mm = self.frame_width_mm + self.frame_bottom_spacing_mm
        self.qr_data = get_qr_data(self.data)


def get_qr_data(data: str) -> QrCodeData:
    qr = qrcode.QRCode(border="0")
    qr.add_data(data)
    qr_data: QrCodeData = qr.get_matrix()

    return qr_data


def make_frame(
    params: QrCodeParamsCalculated,
) -> so.OpenSCADObject:
    frame_2d = so.square([params.frame_width_mm, params.frame_length_mm], center=True)

    for i, (j, k) in enumerate(CORNER_ITER):
        fillet = so.translate(
            [
                j * (params.frame_width_mm / 2 - params.frame_fillet_radius_mm),
                k * (params.frame_length_mm / 2 - params.frame_fillet_radius_mm),
                0,
            ]
        )(
            su.arc_inverted(
                rad=params.frame_fillet_radius_mm,
                start_degrees=i * 90,
                end_degrees=(i + 1) * 90,
                segments=ROUND_SEGMENTS,
            )
        )

        frame_2d = frame_2d - fillet

    frame = so.color(FRAME_COLOR)(
        so.translate([0, 0, -params.frame_thickness_mm])(
            so.linear_extrude(params.frame_thickness_mm)(frame_2d)
        )
    )

    if params.nfc:
        nfc = so.cylinder(
            r=params.nfc_diameter_mm / 2,
            h=params.nfc_thickness_mm,
            segments=ROUND_SEGMENTS,
        )
        nfc = so.translate(
            [0, 0, -params.frame_thickness_mm + params.nfc_base_offset_mm]
        )(nfc)
        frame = frame - nfc

    if params.magnets:
        for j, k in CORNER_ITER:
            magnet = so.cylinder(
                r=params.magnets_diameter_mm / 2,
                h=params.magnets_thickness_mm + 0.1,
                segments=ROUND_SEGMENTS,
            )
            magnet = so.translate(
                [
                    j
                    * (
                        params.frame_width_mm / 2
                        - params.magnets_diameter_mm / 2
                        - params.magnets_inset_mm
                    ),
                    k
                    * (
                        params.frame_length_mm / 2
                        - params.magnets_diameter_mm / 2
                        - params.magnets_inset_mm
                    ),
                    -params.frame_thickness_mm - 0.1,
                ]
            )(magnet)
            frame = frame - magnet

    frame_outline_2d = frame_2d - so.offset(-params.frame_outline_mm)(frame_2d)
    frame_outline = so.color(OUTLINE_COLOR)(
        so.linear_extrude(params.frame_outline_thickness_mm)(frame_outline_2d)
    )

    frame = frame + frame_outline

    return frame


def make_qr_blocks(
    params: QrCodeParamsCalculated,
) -> so.OpenSCADObject:
    data_len = len(params.qr_data)
    block_size = params.qr_size_mm / data_len

    FILLET_LUT = {
        (0, data_len - 1): (1, 1, 0),
        (0, 0): (2, 1, 1),
        (data_len - 1, 0): (3, 0, 1),
    }

    qr_blocks = []
    for i in range(data_len):
        for j in range(data_len):
            if params.qr_data[i][j]:
                x = i * block_size - params.qr_size_mm / 2
                y = j * block_size - params.qr_size_mm / 2

                block = so.square([block_size, block_size])

                fillet = FILLET_LUT.get((i, j))
                if fillet:
                    fillet_obj = su.arc_inverted(
                        rad=block_size,
                        start_degrees=fillet[0] * 90,
                        end_degrees=(fillet[0] + 1) * 90,
                        segments=ROUND_SEGMENTS,
                    )

                    fillet_obj = so.translate(
                        [
                            fillet[1] * block_size,
                            fillet[2] * block_size,
                            0,
                        ]
                    )(fillet_obj)

                    block = block - fillet_obj

                block = so.linear_extrude(params.qr_thickness_mm)(block)
                block = so.translate([x, y, 0])(block)
                block = so.color(QR_COLOR)(block)

                qr_blocks.append(block)

    qr_blocks = so.union()(*qr_blocks)

    return so.rotate([0, 0, 0])(qr_blocks)


def make_titles(
    params: QrCodeParamsCalculated,
) -> so.OpenSCADObject:
    title = so.text(
        params.title,
        size=params.title_size_mm,
        font=params.title_font,
        halign="center",
        valign="baseline",
    )

    title = so.linear_extrude(params.titles_thickness_mm)(title)
    title_width = params.title_size_mm * TITLE_KERNING * len(params.title)

    if params.subtitle:
        subtitle = so.linear_extrude(params.titles_thickness_mm)(
            so.text(
                params.subtitle,
                size=params.subtitle_size_mm,
                font=params.subtitle_font,
                halign="center",
                valign="baseline",
            )
        )

        title = so.translate([0, params.titles_spacing_mm / 2, 0])(title)
        subtitle = so.translate(
            [0, -params.titles_spacing_mm / 2 - params.subtitle_size_mm, 0]
        )(subtitle)

        titles = title + subtitle
        title_width = max(
            title_width, params.subtitle_size_mm * TITLE_KERNING * len(params.subtitle)
        )
    else:
        title = so.translate([0, -params.title_size_mm / 3, 0])(title)
        titles = title

    total_width = params.frame_width_mm + params.qr_border_mm * 2
    text_scale = min(total_width / title_width, 1)
    titles = so.scale([text_scale, text_scale, 1])(titles)

    return so.color(TITLE_COLOR)(titles)


def make_qr_obj(params: QrCodeParamsCalculated) -> so.OpenSCADObject:
    frame = make_frame(params)

    qr_blocks = make_qr_blocks(params)
    qr_blocks = so.translate(
        [
            0,
            ((params.frame_length_mm - params.qr_size_mm) / 2)
            - params.qr_border_mm
            - params.frame_outline_mm,
            0,
        ]
    )(qr_blocks)

    qr_obj = frame + qr_blocks

    if params.title:
        title = make_titles(params)
        title = so.translate(
            [
                0,
                -params.frame_length_mm / 2
                + params.frame_outline_mm
                + params.frame_bottom_spacing_mm / 2
                + params.qr_border_mm / 2,
                0,
            ]
        )(title)

        qr_obj = qr_obj + title

    return qr_obj


def generate_qr_scad(params: QrCodeParams, path: str) -> str:
    qr_params = QrCodeParamsCalculated(params)
    qr_obj = make_qr_obj(qr_params)
    return so.scad_render_to_file(qr_obj, path)
