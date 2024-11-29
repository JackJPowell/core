"""Media player entity for the Playstation Network Integration."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityDescription,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PlaystationNetworkCoordinator
from .coordinator import PlaystationNetworkData
from .entity import PlaystationNetworkEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Media Player Entity Setup."""
    coordinator: PlaystationNetworkCoordinator = config_entry.runtime_data

    if coordinator.data.platform.get("platform") is None:
        username = coordinator.data.username
        _LOGGER.warning(
            "No console found associated with account: %s. -- Skipping creation of media player",
            username,
        )
        return

    async_add_entities([MediaPlayer(coordinator)])


class MediaPlayer(PlaystationNetworkEntity, MediaPlayerEntity):
    """Media player entity representing currently playing game."""

    entity_description = MediaPlayerEntityDescription(
        key="console",
        translation_key="console",
        device_class=MediaPlayerDeviceClass.TV,
    )
    _attr_media_image_remotely_accessible = True
    _attr_translation_key = "playstation"
    _attr_media_content_type = MediaType.GAME

    def __init__(self, coordinator: PlaystationNetworkCoordinator) -> None:
        """Initialize PSN MediaPlayer."""
        super().__init__(coordinator)
        self.psn: PlaystationNetworkData = self.coordinator.data
        if coordinator.config_entry:
            self._attr_unique_id = (
                f"{coordinator.config_entry.unique_id}_{self.entity_description.key}"
            )

    @property
    def state(self) -> MediaPlayerState:
        """Media Player state getter."""
        match self.psn.platform.get("onlineStatus", ""):
            case "online":
                if (
                    self.psn.available is True
                    and self.psn.title_metadata.get("npTitleId") is not None
                ):
                    return MediaPlayerState.PLAYING
                return MediaPlayerState.ON
            case "offline":
                return MediaPlayerState.OFF
            case _:
                return MediaPlayerState.OFF

    @property
    def name(self) -> str:
        """Name getter."""
        return f"{self.psn.platform.get('platform')} Console"

    @property
    def media_title(self) -> str | None:
        """Media title getter."""
        if self.psn.title_metadata.get("npTitleId"):
            return self.psn.title_metadata.get("titleName")
        if self.psn.platform.get("onlineStatus") == "online":
            return None
        return None

    @property
    def media_image_url(self) -> str | None:
        """Media image url getter."""
        if self.psn.title_metadata.get("npTitleId"):
            title = self.psn.title_metadata
            if title.get("format", "").casefold() == "ps5":
                return title.get("conceptIconUrl")

            if title.get("format", "").casefold() == "ps4":
                return title.get("npTitleIconUrl")
        return None

    @property
    def is_on(self) -> bool:
        """Is user available on the Playstation Network."""
        return self.psn.available is True
