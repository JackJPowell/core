"""Coordinator for the Playstation Network Integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from psnawp_api.core.psnawp_exceptions import PSNAWPAuthenticationError
from psnawp_api.models.user import User
from psnawp_api.psn import PlaystationNetwork, PlaystationNetworkData

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
DEVICE_SCAN_INTERVAL = timedelta(seconds=30)


class PlaystationNetworkCoordinator(DataUpdateCoordinator[PlaystationNetworkData]):
    """Data update coordinator for PSN."""

    def __init__(
        self, hass: HomeAssistant, psn: PlaystationNetwork, user: User
    ) -> None:
        """Initialize the Coordinator."""
        super().__init__(
            hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=DEVICE_SCAN_INTERVAL,
        )

        self.hass = hass
        self.user: User = user
        self.psn: PlaystationNetwork = psn

    async def _async_update_data(self) -> PlaystationNetworkData:
        """Get the latest data from the PSN."""
        try:
            return await self.hass.async_add_executor_job(self.psn.get_data)
        except PSNAWPAuthenticationError as error:
            raise UpdateFailed(error) from error
