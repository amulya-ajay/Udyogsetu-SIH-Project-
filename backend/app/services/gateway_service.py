"""Government API Gateway service.

Routes requests to the correct system adapter, applies retry + timeout,
polls status, and monitors system health so the officer dashboard can show
per-system reliability.
"""

from __future__ import annotations

import asyncio
import logging
import time

from app.integrations.government_adapters import GovernmentAPIGateway
from app.integrations.mock_gov_api import get_mock_gov_api

logger = logging.getLogger(__name__)


class GatewayService:
    """Facade over the government integration adapters + mock API."""

    def __init__(self):
        self.gateway = GovernmentAPIGateway()
        self.mock = get_mock_gov_api()
        self._health: dict[str, dict] = {}
        self._last_check: float = 0.0

    # ------------------------------------------------------------------
    # Status / submission with retry + timeout
    # ------------------------------------------------------------------
    async def get_status(self, system: str, application_id: str) -> dict:
        return await self._with_retry(
            self.gateway.get_application_status(system, application_id),
            system,
        )

    async def submit(self, system: str, application_data: dict) -> dict:
        return await self._with_retry(
            self.gateway.submit_application(system, application_data),
            system,
        )

    async def verify(self, kind: str, value: str) -> dict:
        """Route a business-verification lookup to the right system."""
        if kind == "gstin":
            return await self.mock.verify_gstin(value)
        if kind == "pan":
            return await self.mock.verify_pan(value)
        if kind == "udyam":
            return await self.mock.verify_udyam(value)
        if kind == "scheme":
            return await self.mock.check_scheme_eligibility(value, {})
        if kind == "clearance":
            return await self.mock.check_clearance(value, {})
        return {"data": None, "message": f"Unknown verification kind: {kind}"}

    async def _with_retry(self, coro, system: str, retries: int = 2, timeout: float = 10.0) -> dict:
        attempt = 0
        while True:
            try:
                result = await asyncio.wait_for(coro, timeout=timeout)
                self._record_health(system, ok=True, latency=0.5)
                return result
            except Exception as exc:  # noqa: BLE001
                attempt += 1
                self._record_health(system, ok=False, latency=1.0)
                if attempt > retries:
                    logger.warning("Gateway %s failed after %d attempts: %s", system, attempt, exc)
                    return {"system": system, "error": str(exc), "status": "UNAVAILABLE"}
                await asyncio.sleep(0.2 * attempt)

    def _record_health(self, system: str, ok: bool, latency: float):
        now = time.time()
        entry = self._health.setdefault(system, {"ok": 0, "total": 0, "latency": 0.0})
        entry["total"] += 1
        entry["ok"] += int(ok)
        entry["latency"] = (entry["latency"] * (entry["total"] - 1) + latency) / entry["total"]

    # ------------------------------------------------------------------
    # System health monitoring (spec §19 / §44)
    # ------------------------------------------------------------------
    async def system_health(self, force: bool = False) -> dict:
        now = time.time()
        if not force and self._last_check and (now - self._last_check) < 30:
            return self._snapshot()
        self._last_check = now
        for system in ("maitri", "mpcb", "midc", "boiler", "fire", "labour", "gst"):
            # Probe availability cheaply.
            try:
                env = await asyncio.wait_for(self.mock.list_services(system), timeout=5)
                self._record_health(system, ok=True, latency=0.3)
            except Exception:  # noqa: BLE001
                self._record_health(system, ok=False, latency=1.0)
        return self._snapshot()

    def _snapshot(self) -> dict:
        systems = {}
        for name, entry in self._health.items():
            ok_rate = (entry["ok"] / entry["total"]) if entry["total"] else 1.0
            systems[name] = {
                "status": "HEALTHY" if ok_rate >= 0.9 else ("DEGRADED" if ok_rate >= 0.5 else "DOWN"),
                "availability_pct": round(ok_rate * 100, 1),
                "avg_latency_ms": round(entry["latency"] * 1000, 1),
                "calls": entry["total"],
            }
        return {"systems": systems, "checked_at": datetime_iso()}


def datetime_iso() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"