import base64
import io
from typing import List
from urllib.parse import quote

import qrcode
from fastapi import HTTPException

from app.models.temple import Temple
from app.models.temple_timing import TempleTiming
from app.repositories.temple_repo import TempleRepository
from app.schemas.temple import HundiQrOut, TempleUpdate, TimingCreate, TimingUpdate


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
        vpa = temple.upi_vpa if temple else None
        if not temple or not vpa:
            return HundiQrOut(configured=False)

        payee_name = temple.name
        upi_uri = f"upi://pay?pa={quote(vpa)}&pn={quote(payee_name)}&cu=INR&tn={quote('Hundi Donation')}"

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(upi_uri)
        qr.make(fit=True)
        buffered = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(buffered, format="PNG")

        return HundiQrOut(
            configured=True,
            upi_vpa=vpa,
            payee_name=payee_name,
            qr_base64=base64.b64encode(buffered.getvalue()).decode(),
        )

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
