---
name: aidol-event-router
description: Connect Aidol Event Router to a customer's Aidol Room through ALC, operate product pinning, and configure billed Room AI text comment replies through its local MCP.
---

# Aidol Event Router

Use the Aidol Event Router MCP on the customer's Windows computer. It controls the running updated app, not a remote customer's desktop. Start with `router_status`; if unreachable, guide the customer to open Event Router 1.5.9 or newer and reconnect MCP. The Windows customer installer includes Router, the standalone MCP executable and this skill. Run “Kết nối Codex và Claude Code” from Start Menu, then restart the agent. No Python installation is needed for the customer bundle. Older installed executables do not gain this bridge automatically.

## Connect the correct room

ALC is the one-time connection code, not VLC and not an API key. Ask which owned room the customer intends to connect. If Aidol Room MCP or browser tools are available, use their supported operations to open that room and obtain the connection code; otherwise guide the customer to the connection-software button near the top of the room interface. This package does not install the Room web MCP or a browser agent. Do not invent a tool name or extract a different room's code. Check for an appropriate existing lease before renting another. If web login is needed, open a visible browser and direct the customer to sign in in that exact window; signing in to another browser profile does not authenticate the agent session. Verify the signed-in account before proceeding.

Call `router_connect_room` with the ALC; then inspect `router_status` until connection succeeds or an error appears. An accepted asynchronous command is not a connected room. Compare session identity with the intended room. Do not silently replace an existing connection; disconnect only when the customer intends that change. A used/expired code needs a fresh code from the room. Never display codes, tokens or API keys in reports.

If Router requires login, have the customer log in there. Guide the customer for passwords, platform login, two-factor authentication and CAPTCHA; do not ask them to paste passwords into chat.

## Product pinning

Open the proper TikTok or Shopee browser with `router_open_pin_browser`. Ask the customer to sign in and open the correct live product management panel. Enable pinning only when that panel is ready. Reuse the app's existing configuration and product codes.

Record pin sent/failed counters, then submit an authorized test code. Inspect counter changes and ask the customer to verify the visible pinned product. Queue acceptance is not completion. The pin action is **Hiển thị**, changing to **Xóa** when shown; **Di chuyển lên đầu** changes product order and is not pinning. When troubleshooting scanning, test both later codes and returning to an earlier code; scrolling must work both ways. If failure persists, stop retrying and request current panel HTML or a screenshot without secrets.

For an end-to-end script test, use an authorized product transition in the connected Room and check Router's received-reply and pin counters. A manually submitted pin proves only the local pin path. Do not report Room-to-Router delivery as verified from a local test alone.

## Text comment replies and Tun Coin

ALC connects the room's events and pin commands. Text AI replies separately use the customer's **Aidol Room API key `ar_…`**, obtained from `https://room.genaidol.com/#api`. This is not a third-party LLM key. Prefer the customer entering it into the masked API field in Router; `router_save_room_api_key` is available when an authorized secret input mechanism exists. Never read or print the saved key. The app stores it with Windows DPAPI.

Explain that Brain API calls spend **Tun Coin**, including `router_test_brain`. Obtain agreement before passing `allow_tun_coin=true` or starting automatic AI. Saving a key or preparing a prompt does not authorize spending. Reuse explicit authorization already provided for this task.

Use `router_configure_text_replies` to configure the customer's reply rules. It selects comments only, leaves speech off and defaults automatic Enter off. Enable Enter only if the customer wants automatic posting. If other event types or sources are needed, guide the customer through the corresponding Router controls; MCP currently reuses the capture source configured in the UI.

Use `router_position_reply_input` to show the overlay. Ask the customer to place it over the intended comment input. Confirm only after they report it is placed correctly. Check readiness, start text replies with spending consent, and start capture if authorized. Validate with one identifiable comment; inspect capture state, reply sent/failed counters and the actual text in the intended input. If Enter is off, the customer sends the prepared text manually.

Do not enable TTS as a side effect. If the customer specifically wants speech, guide them to choose a voice in Router; this MCP's reply-start path supports text-only mode. Stop via `router_stop_text_replies` when requested; stopping text replies does not stop the customer's livestream.

Report what was verified, which customer step is pending, and any remaining failure. Do not claim a complete live workflow from unit tests or queued commands alone.
