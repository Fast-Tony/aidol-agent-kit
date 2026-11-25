import asyncio
import json
from pathlib import Path
import sys
import unittest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_both_stdio_servers(self):
        root = Path(__file__).parents[1]
        for component, expected in [('room','room_mode_guidance'), ('router','router_status')]:
            params = StdioServerParameters(command=sys.executable, args=[str(root / component / 'server.py')])
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as client:
                    await client.initialize()
                    listing = await client.list_tools()
                    self.assertIn(expected, {tool.name for tool in listing.tools})
                    if component == 'room':
                        response = await client.call_tool(expected, {})
                        self.assertEqual(json.loads(response.content[0].text)['recommended_mode'], 'simple')


if __name__ == '__main__':
    unittest.main()
