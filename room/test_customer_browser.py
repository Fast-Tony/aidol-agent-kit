import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

spec = importlib.util.spec_from_file_location('room_browser_test', Path(__file__).with_name('server.py'))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class CustomerBrowserTest(unittest.IsolatedAsyncioTestCase):
    async def test_no_cdp_opens_visible_customer_browser(self):
        runtime = AsyncMock()
        context = AsyncMock()
        page = AsyncMock()
        context.pages = [page]
        context.browser = AsyncMock()
        runtime.chromium.launch_persistent_context.return_value = context
        startup = AsyncMock()
        startup.start.return_value = runtime
        with patch.dict(os.environ, {'LOCALAPPDATA': 'C:/Aidol-Test-Profile'}, clear=True), patch.object(server, 'async_playwright', return_value=startup):
            actual = await server.current_page()
        self.assertIs(actual, page)
        self.assertFalse(runtime.chromium.launch_persistent_context.call_args.kwargs['headless'])


if __name__ == '__main__':
    unittest.main()
