"""Run with Python and the mcp package; communicates with the running Router."""
import json
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
from mcp.server.fastmcp import FastMCP
from windows_secret import app_data_root, protect


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


mcp = FastMCP('Aidol Event Router', instructions=(
    'Use router_status first. ALC links the live room; an ar_ Room API key separately '
    'pays for Brain text replies in Tun Coin. Explain charges and obtain consent '
    'before enabling AI or testing Brain. Never expose keys. Guide the customer '
    'through login, CAPTCHA and positioning the comment input. Queue acceptance '
    'does not prove a product was pinned; inspect sent/failed counters.'))


def call(action, **arguments):
    try:
        descriptor = json.loads(protect((app_data_root() / 'agent-control.dpapi').read_bytes(), decrypt=True))
        port = descriptor['port']
        if type(port) is not int or not 1024 <= port <= 65535:
            raise ValueError()
        request = Request(f'http://127.0.0.1:{port}/command',
                          data=json.dumps({'action': action, 'arguments': arguments}).encode(),
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + descriptor['token']})
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=45) as response:
            return json.loads(response.read(1024 * 1024))
    except Exception:
        return {'ok': False, 'error': 'Cannot reach updated Event Router. Open it under this Windows user; check status before retrying changes.'}


@mcp.tool()
def router_status() -> dict:
    """Read login, room binding, capture, pin counters and reply readiness; no secrets."""
    return call('status')


@mcp.tool()
def router_connect_room(alc_code: str) -> dict:
    """Exchange the customer's one-time ALC code. Poll status for completion."""
    return call('cloud_connect', code=alc_code)


@mcp.tool()
def router_disconnect_room() -> dict:
    """Explicitly disconnect the current room. A fresh ALC is needed to reconnect."""
    return call('cloud_disconnect')


@mcp.tool()
def router_save_room_api_key(api_key: str) -> dict:
    """Save customer's ar_ Room key with Windows DPAPI; prefer customer entering it in UI."""
    return call('brain_key', key=api_key)


@mcp.tool()
def router_test_brain(allow_tun_coin: bool = False) -> dict:
    """One billed Brain request. Requires customer's agreement to Tun Coin spending."""
    return call('brain_test', allow_tun_coin=allow_tun_coin)


@mcp.tool()
def router_configure_text_replies(prompt: str, press_enter: bool = False) -> dict:
    """Configure Room AI for comments only, speech off. Does not start AI. Enter opt-in."""
    return call('reply_configure', prompt=prompt, press_enter=press_enter)


@mcp.tool()
def router_position_reply_input(confirm_customer_position: bool = False) -> dict:
    """Open positioning overlay, or confirm only after customer has placed it correctly."""
    return call('reply_confirm_position' if confirm_customer_position else 'reply_position')


@mcp.tool()
def router_start_text_replies(allow_tun_coin: bool = False) -> dict:
    """Enable billed text-only replies after customer consent; requires key and confirmed input."""
    return call('reply_start', allow_tun_coin=allow_tun_coin)


@mcp.tool()
def router_stop_text_replies() -> dict:
    """Disable Brain and clear pending typed replies."""
    return call('reply_stop')


@mcp.tool()
def router_open_pin_browser(platform: str = 'tiktok') -> dict:
    """Open isolated TikTok/Shopee browser; customer signs in and opens live product panel."""
    return call('pin_browser', platform=platform)


@mcp.tool()
def router_enable_pinning(platform: str = 'tiktok') -> dict:
    """Enable pin worker after customer's live product panel is ready."""
    return call('pin_enable', platform=platform)


@mcp.tool()
def router_pin_product(pin_code: str, platform: str = 'tiktok', product_id: str = '', product_name: str = '') -> dict:
    """Queue a pin. Verify counter delta and visible Display/Delete state before claiming success."""
    return call('pin_submit', pin_code=pin_code, platform=platform,
                product_id=product_id, product_name=product_name)


@mcp.tool()
def router_stop_pinning() -> dict:
    """Stop product pinning without disconnecting the room."""
    return call('pin_stop')


@mcp.tool()
def router_capture(start: bool = True) -> dict:
    """Start/stop capture using the platform/source currently configured in Router UI."""
    return call('capture_start' if start else 'capture_stop')


if __name__ == '__main__':
    mcp.run(transport='stdio')
