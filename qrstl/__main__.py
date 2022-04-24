from .qr import QrCodeParams, generate_qr_scad


def main():
    qr_params = QrCodeParams(
        data="Test",
        title="Test",
        subtitle="Hello!",
        frame_outline_mm=0,
        frame_thickness_mm=2,
        nfc_base_offset_mm=0.6,
        nfc_thickness_mm=0.6,
        qr_border_mm=2.5,
        qr_size_mm=50,
        qr_thickness_mm=0.6,
        titles_thickness_mm=0.6,
    )

    generate_qr_scad(qr_params, "test.scad")


if __name__ == "__main__":
    main()
