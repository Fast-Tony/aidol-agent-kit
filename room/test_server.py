import importlib.util
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

spec = importlib.util.spec_from_file_location('live_mcp', Path(__file__).with_name('server.py'))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class ContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_rental_requires_customer_mode_choice(self):
        with self.assertRaisesRegex(ValueError, 'Choose Simple or Studio Pro'):
            await server.room_rent(103, 'mode-choice-test', 4000000)
        with self.assertRaisesRegex(ValueError, 'Choose Simple or Studio Pro'):
            await server.room_rent_ui('AR-099')

    async def test_mode_guidance_explains_output_and_beta(self):
        guidance = await server.room_mode_guidance()
        self.assertEqual(guidance['recommended_mode'], 'simple')
        self.assertFalse(guidance['modes']['simple']['removes_background'])
        self.assertFalse(guidance['modes']['simple']['templates'])
        self.assertTrue(guidance['modes']['pro']['beta'])
        self.assertEqual(guidance['modes']['pro']['output_resolution'], '720p')
        self.assertTrue(guidance['ask_customer'])

    async def test_paid_confirmation_requires_authorization(self):
        with self.assertRaisesRegex(ValueError, 'charge coins'):
            await server.ui_click('button', 'Xác nhận thuê')

    async def test_no_generic_destructive_controls(self):
        with self.assertRaisesRegex(ValueError, 'Destructive'):
            await server.ui_click('button', 'Xóa phòng live')

    async def test_no_upload_without_explicit_media_root(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'AIDOL_UPLOAD_ROOT'):
                await server.ui_upload('C:/private.mp4')

    async def test_output_not_returned_while_preparing(self):
        page = AsyncMock()
        indicator = AsyncMock()
        indicator.get_attribute.return_value = 'preparing'
        page.locator = lambda selector: indicator
        with patch.object(server, 'current_page', AsyncMock(return_value=page)):
            result = await server.studio_output()
        self.assertFalse(result['ready'])
        self.assertNotIn('browser_source_url', result)

    async def test_output_uses_copy_button_payload(self):
        page = AsyncMock()
        indicator = AsyncMock()
        indicator.get_attribute.return_value = 'live'
        page.locator = lambda selector: indicator
        expected = 'https://room.genaidol.com/studio-live/owned/player?token=from-button'
        with patch.object(server, 'current_page', AsyncMock(return_value=page)), patch.object(server, 'copy_obs_link', AsyncMock(return_value=expected), create=True) as copy:
            result = await server.studio_output()
        copy.assert_awaited_once_with(page)
        self.assertEqual(result['browser_source_url'], expected)
        self.assertEqual(result['link_source'], 'obs_copy_button')
        self.assertFalse(result['playback_verified'])

    async def test_output_never_falls_back_when_copy_fails(self):
        page = AsyncMock()
        indicator = AsyncMock()
        indicator.get_attribute.return_value = 'live'
        page.locator = lambda selector: indicator
        with patch.object(server, 'current_page', AsyncMock(return_value=page)), patch.object(server, 'copy_obs_link', AsyncMock(side_effect=ValueError('copy failed')), create=True):
            result = await server.studio_output()
        self.assertFalse(result['ready'])
        self.assertNotIn('browser_source_url', result)

    async def test_start_idempotent_when_live(self):
        page = AsyncMock()
        indicator = AsyncMock()
        indicator.get_attribute.return_value = 'live'
        page.locator = lambda selector: indicator
        with patch.object(server, 'current_page', AsyncMock(return_value=page)):
            result = await server.studio_start()
        self.assertTrue(result['already_running'])
        page.get_by_role.assert_not_called()

    async def test_tool_catalog(self):
        tools = await server.mcp.list_tools()
        names = {tool.name for tool in tools}
        self.assertTrue({'room_rent_ui', 'ui_upload', 'ui_set', 'studio_layer', 'studio_output'} <= names)


if __name__ == '__main__':
    unittest.main()
