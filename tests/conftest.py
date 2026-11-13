"""Pytest configuration and Home Assistant mock fallback for unit tests."""

from __future__ import annotations

import asyncio
import sys
import types
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from datetime import timedelta
    import logging

try:
    import homeassistant  # noqa: F401
except ImportError:

    class _DummyConfigFlow:
        """Minimal stub for Home Assistant ConfigFlow."""

        def __init_subclass__(cls, **kwargs: Any) -> None:
            """Accept domain keyword argument on subclassing."""

        def __init__(self) -> None:
            """Initialize dummy config flow."""
            self.hass = MagicMock()
            self.hass.async_add_executor_job = AsyncMock(
                side_effect=lambda func, *args: func(*args)
            )
            self._unique_id: str | None = None
            self._reconfigure_entry = MagicMock()

        async def async_set_unique_id(self, unique_id: str) -> None:
            """Store unique ID."""
            self._unique_id = unique_id

        def _abort_if_unique_id_configured(self) -> None:
            """No-op duplicate check."""

        def _get_reconfigure_entry(self) -> Any:
            """Return mock reconfigure entry."""
            return self._reconfigure_entry

        def async_create_entry(
            self, *, title: str, data: dict[str, Any]
        ) -> dict[str, Any]:
            """Return create_entry result dict."""
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(
            self,
            *,
            step_id: str,
            data_schema: Any = None,
            errors: dict[str, str] | None = None,
        ) -> dict[str, Any]:
            """Return form result dict."""
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
            }

        def async_update_reload_and_abort(
            self, entry: Any, *, data_updates: dict[str, Any]
        ) -> dict[str, Any]:
            """Return abort result dict after updating entry."""
            return {
                "type": "abort",
                "reason": "reconfigure_successful",
                "data_updates": data_updates,
            }

    class _DummyOptionsFlow:
        """Minimal stub for Home Assistant OptionsFlow."""

        def __init__(self) -> None:
            """Initialize dummy options flow."""
            self.config_entry = MagicMock()
            self.config_entry.options = {}

        def async_create_entry(
            self, *, title: str, data: dict[str, Any]
        ) -> dict[str, Any]:
            """Return create_entry result dict."""
            return {"type": "create_entry", "title": title, "data": data}

        def async_show_form(
            self, *, step_id: str, data_schema: Any = None
        ) -> dict[str, Any]:
            """Return form result dict."""
            return {"type": "form", "step_id": step_id, "data_schema": data_schema}

    class _DummyCoordinatorEntity:
        """Minimal stub for CoordinatorEntity."""

        def __class_getitem__(cls, item: Any) -> type[_DummyCoordinatorEntity]:
            """Support generic subscripting."""
            return cls

        def __init__(self, coordinator: Any) -> None:
            """Store coordinator reference."""
            self.coordinator = coordinator

    class _DummySelectEntity:
        """Minimal stub for SelectEntity."""

        _attr_unique_id: str | None = None
        _attr_options: list[str] = []
        _attr_device_info: dict[str, Any] | None = None

        @property
        def unique_id(self) -> str | None:
            """Return unique ID."""
            return self._attr_unique_id

        @property
        def options(self) -> list[str]:
            """Return available options."""
            return self._attr_options

        @property
        def device_info(self) -> dict[str, Any] | None:
            """Return device info."""
            return self._attr_device_info

    class _DummyDataUpdateCoordinator:
        """Minimal stub matching Home Assistant DataUpdateCoordinator signature."""

        def __class_getitem__(cls, item: Any) -> type[_DummyDataUpdateCoordinator]:
            """Support generic subscripting."""
            return cls

        def __init__(  # noqa: PLR0913
            self,
            hass: Any,
            logger: logging.Logger,
            *,
            name: str,
            update_interval: timedelta | None = None,
            update_method: Callable[[], Awaitable[Any]] | None = None,
            setup_method: Callable[[], Awaitable[None]] | None = None,
            request_refresh_debouncer: Any = None,
            always_refresh: bool = False,
            config_entry: Any = None,
            batch_update: bool = False,
        ) -> None:
            """Initialize coordinator stub with full HA constructor signature."""
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.update_method = update_method
            self.setup_method = setup_method
            self.request_refresh_debouncer = request_refresh_debouncer
            self.always_refresh = always_refresh
            self.config_entry = config_entry
            self.batch_update = batch_update
            self.data: Any = None
            self.last_update_success: bool = True

        async def async_config_entry_first_refresh(self) -> None:
            """Perform initial refresh stub."""

    def _register_module(name: str, attrs: dict[str, Any] | None = None) -> None:
        mod = types.ModuleType(name)
        if attrs:
            for key, value in attrs.items():
                setattr(mod, key, value)
        sys.modules[name] = mod

    _register_module("homeassistant")
    _register_module(
        "homeassistant.config_entries",
        {
            "ConfigEntry": MagicMock,
            "ConfigFlow": _DummyConfigFlow,
            "ConfigFlowResult": dict,
            "OptionsFlow": _DummyOptionsFlow,
        },
    )
    _register_module(
        "homeassistant.core",
        {"HomeAssistant": MagicMock, "callback": lambda func: func},
    )
    _register_module("homeassistant.core_config", {"Config": MagicMock})
    _register_module("homeassistant.exceptions", {"ConfigEntryNotReady": Exception})
    _register_module("homeassistant.helpers")
    _register_module(
        "homeassistant.helpers.device_registry",
        {
            "CONNECTION_NETWORK_MAC": "mac",
            "DeviceInfo": lambda **kwargs: kwargs,
            "async_get": MagicMock(),
        },
    )
    _register_module(
        "homeassistant.helpers.entity_platform", {"AddEntitiesCallback": Any}
    )
    _register_module(
        "homeassistant.helpers.selector",
        {
            "NumberSelector": MagicMock(),
            "NumberSelectorConfig": MagicMock(),
            "NumberSelectorMode": MagicMock(),
            "TextSelector": MagicMock(),
            "TextSelectorConfig": MagicMock(),
            "TextSelectorType": MagicMock(),
        },
    )
    _register_module(
        "homeassistant.helpers.update_coordinator",
        {
            "DataUpdateCoordinator": _DummyDataUpdateCoordinator,
            "UpdateFailed": Exception,
            "CoordinatorEntity": _DummyCoordinatorEntity,
        },
    )
    _register_module("homeassistant.loader", {"async_get_integration": AsyncMock()})
    _register_module("homeassistant.components")
    _register_module(
        "homeassistant.components.select", {"SelectEntity": _DummySelectEntity}
    )

try:
    from homeassistant.config_entries import (
        ConfigFlow as _RealConfigFlow,
        OptionsFlow as _RealOptionsFlow,
    )
    from homeassistant.helpers import frame as _ha_frame

    @pytest.fixture(autouse=True)
    async def _setup_real_ha_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
        """Initialize Home Assistant helpers and flow attributes in container."""
        hass = MagicMock()
        hass.loop = asyncio.get_running_loop()
        hass.async_add_executor_job = AsyncMock(
            side_effect=lambda func, *args: func(*args)
        )
        hass.config_entries.flow.async_progress_by_handler.return_value = []
        hass.config_entries.async_entry_for_domain_unique_id.return_value = None

        reconfigure_entry = MagicMock()
        reconfigure_entry.options = {}
        reconfigure_entry.update_listeners = []
        hass.config_entries.async_get_known_entry.return_value = reconfigure_entry

        _ha_frame.async_setup(hass)
        monkeypatch.setattr(_RealConfigFlow, "hass", hass, raising=False)
        monkeypatch.setattr(_RealConfigFlow, "context", {}, raising=False)
        monkeypatch.setattr(
            _RealConfigFlow, "_reconfigure_entry_id", "entry_reconf_123", raising=False
        )
        monkeypatch.setattr(_RealOptionsFlow, "hass", hass, raising=False)
        monkeypatch.setattr(
            _RealOptionsFlow, "handler", "entry_reconf_123", raising=False
        )
except ImportError:
    pass
