import random
from datetime import datetime
from app.config import get_settings
from app.models.impact import SatelliteContext

class SatelliteClient:
    def __init__(self):
        self.use_mock = get_settings().use_mock_satellite

    async def get_satellite_context(self, lat, lon, timestamp=None) -> SatelliteContext:
        timestamp = timestamp or datetime.utcnow()
        return SatelliteContext(latitude=lat, longitude=lon, timestamp=timestamp, cloud_coverage=random.uniform(0, 100), metadata={"mock": True})

_client = None
def get_satellite_client():
    global _client
    if not _client: _client = SatelliteClient()
    return _client
