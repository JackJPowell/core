"""Coordinator for the Playstation Network Integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from psnawp_api.core.psnawp_exceptions import PSNAWPAuthenticationError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEVICE_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class PlaystationNetworkData:
    """Dataclass representing data retrieved from the Playstation Network api."""

    presence: dict
    username: str
    title_metadata: dict
    title_details: dict
    platform: dict
    available: bool
    online_status: bool
    recent_titles: list
    country: str | None
    language: str | None


class PlaystationNetworkCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for PSN."""

    def __init__(self, hass: HomeAssistant, api, user, client) -> None:
        """Initialize the Coordinator."""
        super().__init__(
            hass,
            name=DOMAIN,
            logger=_LOGGER,
            update_interval=DEVICE_SCAN_INTERVAL,
        )

        self.api = api
        self.user = user
        self.client = client
        self.psn = PlaystationNetworkData({}, "", {}, {}, {}, False, False, [], "", "")

    async def _async_update_data(self) -> dict[str, Any]:
        """Get the latest data from the PSN."""
        try:
            self.psn.username = self.user.online_id
            self.psn.presence = await self.hass.async_add_executor_job(
                self.user.get_presence
            )

            self.psn.available = (
                self.psn.presence.get("basicPresence", {}).get("availability")
                == "availableToPlay"
            )
            self.psn.platform = self.psn.presence.get("basicPresence", {}).get(
                "primaryPlatformInfo"
            )
            try:
                self.psn.title_metadata = self.psn.presence.get(
                    "basicPresence", {}
                ).get("gameTitleInfoList")[0]
            except Exception:  # noqa: BLE001
                self.psn.title_metadata = {}

            self.psn.country = self.hass.config.country
            self.psn.language = self.hass.config.language

            if (
                self.psn.available is True
                and self.psn.title_metadata.get("npTitleId") is not None
            ):
                title_id = self.psn.title_metadata.get("npTitleId")
                title = await self.hass.async_add_executor_job(
                    lambda: self.api.game_title(title_id, "me")
                )
                ## Attempt to pull details with user's country and language code
                self.psn.title_details = await self.hass.async_add_executor_job(
                    lambda: title.get_details(
                        self.hass.config.country, self.hass.config.language
                    )
                )
                ## If we receive an error, fall back to english
                if self.psn.title_details[0].get("errorCode") is not None:
                    self.psn.title_details = await self.hass.async_add_executor_job(
                        title.get_details
                    )

                titles_with_stats = await self.hass.async_add_executor_job(
                    lambda: self.client.title_stats(limit=3, page_size=3)
                )
                await self.hass.async_add_executor_job(
                    lambda: self._get_titles(titles_with_stats)
                )

            return self.data  # noqa: TRY300
        except PSNAWPAuthenticationError as error:
            raise UpdateFailed(error) from error

    def _get_titles(self, titles):
        for title in titles:
            self.psn.recent_titles.append(title)
