from unittest.mock import patch

import pytest

from core.wifi_tunnel import WifiTunnelRuntimeError, validate_wifi_tunnel_runtime


def test_wifi_tunnel_runtime_accepts_python_313_tls_psk() -> None:
    validate_wifi_tunnel_runtime()


def test_wifi_tunnel_runtime_rejects_older_python() -> None:
    with patch("core.wifi_tunnel.sys.version_info", (3, 12, 10)):
        with pytest.raises(WifiTunnelRuntimeError, match="Python 3.13"):
            validate_wifi_tunnel_runtime()
