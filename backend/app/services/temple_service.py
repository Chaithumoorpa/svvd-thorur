import base64
import io
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote

import qrcode
from fastapi import HTTPException
from PIL import Image, ImageDraw

from app.models.temple import Temple
from app.models.temple_timing import TempleTiming
from app.repositories.temple_repo import TempleRepository
from app.schemas.temple import HundiQrOut, TempleUpdate, TimingCreate, TimingUpdate


LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
# Share of the QR's width the centre logo may cover. Error correction H
# recovers ~30% damaged codewords; a 22%-wide disc hides under 5% of the
# area, leaving a wide margin for print smudges and cheap phone cameras.
LOGO_WIDTH_SHARE = 0.22


@lru_cache(maxsize=1)
def _logo() -> Optional[Image.Image]:
    try:
        return Image.open(LOGO_PATH).convert("RGBA")
    except OSError:
        return None


WEB_BOX_SIZE = 10    # ~650px: crisp on any screen
PRINT_BOX_SIZE = 16  # ~1040px: sharp at 12cm on an A4 poster


def upi_qr_png(data: str, box_size: int = WEB_BOX_SIZE) -> bytes:
    """A QR code for `data` with the temple logo in the middle."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=box_size, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    logo = _logo()
    if logo is not None:
        code_px = qr.modules_count * box_size
        size = int(code_px * LOGO_WIDTH_SHARE)
        cx, cy = img.size[0] // 2, img.size[1] // 2
        # White disc (one module wider than the logo) so the logo's dark rim
        # doesn't merge with the modules around it.
        r = size // 2 + box_size
        ImageDraw.Draw(img).ellipse((cx - r, cy - r, cx + r, cy + r), fill="white")
        mark = logo.resize((size, size), Image.LANCZOS)
        img.paste(mark, (cx - size // 2, cy - size // 2), mark)

    out = io.BytesIO()
    # 64 colours keep the logo's gold gradient and cut the PNG ~3x (the web
    # size is ~12KB) - the modules are pure black/white either way.
    img.quantize(colors=64, method=Image.Quantize.MEDIANCUT).save(out, format="PNG", optimize=True)
    return out.getvalue()


class TempleService:
    def __init__(self, repository: TempleRepository):
        self.repository = repository

    # ---- profile -------------------------------------------------------------------
    def get_profile(self) -> Temple:
        temple = self.repository.get_active()
        if not temple:
            raise HTTPException(status_code=404, detail="Temple profile has not been set up yet")
        return temple

    def update_profile(self, data: TempleUpdate) -> Temple:
        fields = data.model_dump(exclude_unset=True)
        temple = self.repository.get_active()
        if not temple:
            if not fields.get("name"):
                raise HTTPException(status_code=400, detail="Temple name is required")
            temple = Temple(name=fields["name"])
        for key, value in fields.items():
            if key == "name" and not value:
                continue  # name is mandatory; ignore attempts to blank it
            setattr(temple, key, value)
        return self.repository.save(temple)

    # ---- e-Hundi ---------------------------------------------------------------------
    def get_hundi_qr(self) -> HundiQrOut:
        """A UPI deep-link QR built from the temple's own VPA - scanning it pays
        the temple directly through the devotee's own UPI app. Nothing here
        touches a payment gateway or this backend's database; it is the exact
        same direct transfer as paying the physical Hundi box, just with a
        QR code instead of cash."""
        temple = self.repository.get_active()
        upi_uri = self._upi_uri(temple)
        if not upi_uri:
            return HundiQrOut(configured=False)

        return HundiQrOut(
            configured=True,
            upi_vpa=temple.upi_vpa,
            payee_name=self._payee_name(temple),
            qr_base64=base64.b64encode(upi_qr_png(upi_uri)).decode(),
            upi_uri=upi_uri,
            registration_number=temple.registration_number,
            pan_number=temple.pan_number,
            eighty_g_number=temple.eighty_g_number,
        )

    def hundi_qr_print_png(self) -> Optional[bytes]:
        """The same QR at poster resolution, or None when no UPI ID is set."""
        upi_uri = self._upi_uri(self.repository.get_active())
        return upi_qr_png(upi_uri, box_size=PRINT_BOX_SIZE) if upi_uri else None

    @staticmethod
    def _payee_name(temple: Temple) -> str:
        return temple.bank_account_name or temple.name

    @classmethod
    def _upi_uri(cls, temple: Optional[Temple]) -> Optional[str]:
        if not temple or not temple.upi_vpa:
            return None
        # Plain pay-to-VPA intent (payee, name, currency): what every UPI app
        # accepts for a bank-issued temple VPA, with no amount so the devotee
        # chooses their own offering.
        return f"upi://pay?pa={quote(temple.upi_vpa, safe='@')}&pn={quote(cls._payee_name(temple))}&cu=INR"

    # ---- timings -------------------------------------------------------------------
    def list_timings(self, active_only: bool = True) -> List[TempleTiming]:
        return self.repository.list_timings(active_only)

    def _get_timing(self, timing_id: int) -> TempleTiming:
        timing = self.repository.get_timing(timing_id)
        if not timing:
            raise HTTPException(status_code=404, detail="Timing not found")
        return timing

    def create_timing(self, data: TimingCreate) -> TempleTiming:
        return self.repository.save_timing(TempleTiming(**data.model_dump()))

    def update_timing(self, timing_id: int, data: TimingUpdate) -> TempleTiming:
        timing = self._get_timing(timing_id)
        fields = data.model_dump(exclude_unset=True)
        start = fields.get("start_time", timing.start_time)
        end = fields.get("end_time", timing.end_time)
        if end <= start:  # validate the merged result BEFORE touching the row
            raise HTTPException(status_code=422, detail="End time must be after start time")
        for key, value in fields.items():
            setattr(timing, key, value)
        return self.repository.save_timing(timing)

    def delete_timing(self, timing_id: int) -> TempleTiming:
        timing = self._get_timing(timing_id)
        self.repository.delete_timing(timing)
        return timing
