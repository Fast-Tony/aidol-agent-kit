import asyncio
import os
import json
import re
from pathlib import Path
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright


@asynccontextmanager
async def lifespan(application):
    try:
        yield {}
    finally:
        if page is not None and not page.is_closed():
            await page.close()
        if customer_context is not None:
            await customer_context.close()
        if runtime is not None:
            await runtime.stop()


mcp = FastMCP('Aidol Room Live', lifespan=lifespan, instructions='Before renting or setting up a new customer live, call room_mode_guidance and ask the customer to choose Simple or Studio Pro unless they already chose. Recommend Simple for basic character livestreams. Studio Pro is beta, may be unstable, and outputs only 720p. Preserve the chosen mode when reusing rooms.')
lock = asyncio.Lock()
runtime = None
browser = None
page = None
customer_context = None
origin = 'https://room.genaidol.com'


async def current_page():
    global runtime, browser, page, customer_context
    if page is not None and not page.is_closed():
        return page
    endpoint = os.environ.get('AIDOL_BROWSER_CDP', '')
    if not endpoint:
        runtime = await async_playwright().start()
        profile = Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.local/share') / 'AidolAgent' / 'RoomBrowser'
        customer_context = await runtime.chromium.launch_persistent_context(
            str(profile), channel='chrome', headless=False, args=['--no-first-run'])
        browser = customer_context.browser
        page = customer_context.pages[0] if customer_context.pages else await customer_context.new_page()
        await page.goto(origin, wait_until='domcontentloaded')
        return page
    parsed = urlsplit(endpoint)
    if parsed.hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('CDP must use a local browser endpoint.')
    runtime = await async_playwright().start()
    browser = await runtime.chromium.connect_over_cdp(endpoint)
    context = browser.contexts[0]
    page = await context.new_page()
    await page.goto(origin, wait_until='domcontentloaded')
    return page


async def view():
    active = await current_page()
    controls = await active.locator('button,input,select,textarea,a').evaluate_all('''elements=>elements.map(element=>({role:element.tagName.toLowerCase(),label:element.getAttribute('aria-label')||element.innerText||element.placeholder||element.name||element.id,disabled:element.disabled||false,type:element.type})).filter(item=>item.label)''')
    return {'url': active.url, 'text': (await active.locator('body').inner_text())[:24000], 'controls': controls}


async def account_api(path, method='GET', body=None):
    active = await current_page()
    if urlsplit(active.url).netloc != 'room.genaidol.com':
        raise ValueError('Open Aidol Room before using account tools.')
    result = await active.evaluate('''async ({path,method,body})=>{
      const csrf=decodeURIComponent(document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith('aidol_room_csrf='))?.split('=').slice(1).join('=')||'');
      const response=await fetch(path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},...(body?{body:JSON.stringify(body)}:{})});
      const text=await response.text();let data;try{data=JSON.parse(text)}catch{data={message:text.slice(0,300)}};
      return {status:response.status,data};
    }''', {'path': path, 'method': method, 'body': body})
    if result['status'] >= 400:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    return result


@mcp.tool()
async def account_inventory(kind: str = 'leases', page_number: int = 1) -> dict:
    """List the authenticated customer's rooms, leases, characters or saved personal rooms."""
    paths = {'leases': '/api/leases', 'characters': '/api/studio/aidols', 'personal': '/api/personal-rooms', 'rooms': '/api/rooms?page=' + str(max(1, page_number))}
    if kind not in paths:
        raise ValueError('kind must be leases, characters, personal or rooms.')
    async with lock:
        return await account_api(paths[kind])


@mcp.tool()
async def room_mode_guidance() -> dict:
    """Explain Simple versus Studio Pro before asking the customer to choose a mode. Does not rent or change a room."""
    return {
        'ask_customer': True,
        'recommended_mode': 'simple',
        'question': 'Bạn muốn dùng Simple hay Studio Pro? Nếu chỉ cần nhân vật nói và phản hồi bình luận/sự kiện, tôi khuyến nghị Simple. Studio Pro dành cho thiết kế bố cục ngay trên web, hiện còn beta, có thể chưa ổn định và chỉ xuất 720p.',
        'modes': {
            'simple': {
                'name': 'Simple', 'removes_background': False, 'templates': False,
                'description': 'Đầu ra chỉ có nhân vật nói liên tục, nhép môi theo âm thanh và có thể phản hồi bình luận cùng các sự kiện được cấu hình. Nếu video nhân vật có nền xanh thì đầu ra vẫn giữ nền xanh; khách có thể xóa nền và bố trí cảnh trong OBS của họ.',
            },
            'pro': {
                'name': 'Studio Pro', 'beta': True, 'output_resolution': '720p', 'templates': True,
                'description': 'Thiết kế template và bố cục trực tiếp trên Studio web, thêm các thành phần và chuyển thiết kế theo kịch bản. Bản beta có thể chưa ổn định; chỉ xuất 720p.',
            },
        },
        'instruction': 'Ask once before new setup; reuse an explicit choice already given. Do not silently choose Pro or change an existing saved room mode. Live display mode is separate from standard/natural lipsync model.',
    }


@mcp.tool()
async def room_rent(room_id: int, idempotency_key: str, authorized_first_hour_coins: int, mode: str = '') -> dict:
    """Rent an available room using its API ID and a stable retry key, within the authorized displayed first-hour price."""
    if mode not in ('simple', 'pro'):
        raise ValueError('Choose Simple or Studio Pro with the customer first; call room_mode_guidance. Studio Pro is beta and 720p only.')
    if room_id < 1 or not 8 <= len(idempotency_key) <= 160:
        raise ValueError('Invalid rental parameters.')
    async with lock:
        selected = None
        for number in range(1, 30):
            listing = (await account_api('/api/rooms?page=' + str(number)))['data']
            selected = next((item for item in listing.get('rooms', []) if item['id'] == room_id), None)
            if selected or not listing.get('has_more'):
                break
        if not selected or not selected.get('available'):
            raise ValueError('Room is not available. Inspect leases before retrying.')
        price = selected.get('rate_per_hour')
        if not isinstance(price, (int, float)) or price <= 0 or price > authorized_first_hour_coins:
            raise ValueError('Room price exceeds the authorized budget.')
        return await account_api('/api/rooms/' + str(room_id) + '/rent', 'POST', {'studio_mode': mode, 'idempotency_key': idempotency_key})


@mcp.tool()
async def room_rent_ui(room_code: str, mode: str = '') -> dict:
    """Open a room rental dialog and select mode. Does not confirm or charge; inspect its price before ui_click confirmation."""
    if mode not in ('simple', 'pro'):
        raise ValueError('Choose Simple or Studio Pro with the customer first; call room_mode_guidance. Studio Pro is beta and 720p only.')
    if not re.fullmatch('AR-[0-9]{3}', room_code):
        raise ValueError('Invalid room code or mode.')
    async with lock:
        active = await current_page()
        await active.goto(origin + '/#rooms', wait_until='domcontentloaded')
        heading = active.get_by_role('heading', name=room_code, exact=True)
        card = heading.locator('xpath=..')
        for depth in range(5):
            button = card.get_by_role('button', name=re.compile('Tạo phòng|Thuê ngay|Thuê phòng'))
            if await button.count() == 1:
                await button.click()
                break
            card = card.locator('xpath=..')
        else:
            raise ValueError('Cannot uniquely locate room rental button. Inspect the UI.')
        await active.get_by_text('Studio Pro' if mode == 'pro' else 'Simple', exact=True).click()
        return await view()


@mcp.tool()
async def ui_click(role: str, name: str, authorized_paid_action: bool = False) -> dict:
    """Click one uniquely named visible control. Paid confirmation requires prior user authorization; no automatic retries."""
    if role not in ('button', 'link', 'radio', 'checkbox', 'tab'):
        raise ValueError('Unsupported control role.')
    if re.search('xác nhận thuê|đồng ý tạo|tính phí|thanh toán', name, re.I) and not authorized_paid_action:
        raise ValueError('This action can charge coins. Set authorized_paid_action only within the user-authorized budget.')
    if re.search('xóa|đăng xuất|delete', name, re.I):
        raise ValueError('Destructive controls are not exposed by this tool.')
    async with lock:
        active = await current_page()
        target = active.get_by_role(role, name=name, exact=True)
        if await target.count() != 1:
            raise ValueError('Control is missing or ambiguous. Inspect first.')
        await target.click()
        return await view()


@mcp.tool()
async def ui_set(label: str, value: str, kind: str = 'text') -> dict:
    """Set a uniquely labelled real form field for scripts, voice, name, speed or mode. Uses actual UI change events."""
    async with lock:
        active = await current_page()
        target = active.get_by_label(label, exact=True)
        if await target.count() == 0:
            target = active.get_by_placeholder(label, exact=True)
        if await target.count() != 1:
            raise ValueError('Field is missing or ambiguous. Inspect first.')
        if kind == 'select':
            await target.select_option(label=value)
        elif kind == 'check':
            if value not in ('true', 'false'):
                raise ValueError('Checkbox value must be true or false.')
            await target.set_checked(value == 'true')
        elif kind == 'text':
            await target.fill(value)
            await target.press('Tab')
        else:
            raise ValueError('kind must be text, select or check.')
        return await view()


@mcp.tool()
async def studio_character(name: str) -> dict:
    """Select a unique eligible character card by its exact visible character name."""
    async with lock:
        active = await current_page()
        await active.get_by_role('button', name='Nhân vật', exact=True).click()
        card = active.locator('button[data-character-id]').filter(has_text=name)
        if await card.count() != 1:
            raise ValueError('Character card is missing or ambiguous.')
        await card.click()
        return await view()


@mcp.tool()
async def ui_upload(file_path: str, input_label: str = '') -> dict:
    """Upload an authorized local video/image/audio through a real file input; use the creation confirmation separately."""
    root = os.environ.get('AIDOL_UPLOAD_ROOT', '')
    if not root:
        raise ValueError('Set AIDOL_UPLOAD_ROOT to the directory of user-authorized media.')
    target = Path(file_path).resolve()
    if not target.is_relative_to(Path(root).resolve()) or not target.is_file():
        raise ValueError('File must exist within AIDOL_UPLOAD_ROOT.')
    if target.suffix.lower() not in ('.mp4', '.webm', '.mov', '.png', '.jpg', '.jpeg', '.webp', '.mp3', '.wav', '.m4a'):
        raise ValueError('Unsupported media format.')
    async with lock:
        active = await current_page()
        control = active.get_by_label(input_label, exact=True) if input_label else active.locator('input[type=file]')
        if await control.count() != 1:
            raise ValueError('Specify the exact file input label.')
        await control.set_input_files(str(target))
        return await view()


@mcp.tool()
async def studio_layer(selector: str, x_percent: float, y_percent: float, width_percent: float, visible: bool = True) -> dict:
    """Position a single existing layer inside the Studio stage. Add media/text through UI first, then save."""
    if not 0 <= x_percent <= 100 or not 0 <= y_percent <= 100 or not 1 <= width_percent <= 100:
        raise ValueError('Positions must be 0–100 and width 1–100 percent.')
    async with lock:
        active = await current_page()
        return await active.evaluate('''({selector,x,y,width,visible})=>{
          const stage=document.querySelector('#stage');if(!stage)throw Error('Studio stage not found');
          const matches=stage.querySelectorAll(selector);if(matches.length!==1)throw Error('Layer must be unique');
          const layer=matches[0];if(!layer.classList.contains('layer'))throw Error('Select a layer root');
          layer.style.left=x+'%';layer.style.top=y+'%';layer.style.width=width+'%';layer.style.display=visible?'':'none';
          layer.dispatchEvent(new Event('change',{bubbles:true}));return {edited:true,save_required:true};
        }''', {'selector': selector, 'x': x_percent, 'y': y_percent, 'width': width_percent, 'visible': visible})


@mcp.tool()
async def room_inspect() -> dict:
    """Read the current customer UI, available controls, setup errors and live status."""
    async with lock:
        return await view()


@mcp.tool()
async def room_open(section: str = 'rooms', lease_id: str = '') -> dict:
    """Open rooms, personal rooms, character library or an owned Studio lease. Does not rent."""
    paths = {'rooms': '/#rooms', 'characters': '/studio-aidol', 'personal': '/#personal'}
    async with lock:
        active = await current_page()
        if section == 'studio':
            if not lease_id or any(character not in '0123456789abcdef' for character in lease_id) or len(lease_id) != 32:
                raise ValueError('A valid lease_id is required.')
            path = '/aidol-room/static/scene-editor-preview/unified.html?lease=' + lease_id
        elif section in paths:
            path = paths[section]
        else:
            raise ValueError('section must be rooms, personal, characters or studio.')
        await active.goto(origin + path, wait_until='domcontentloaded')
        return await view()


@mcp.tool()
async def studio_tab(name: str) -> dict:
    """Select a Studio tab; inspect afterwards to read the actual options."""
    if name not in ('Nhân vật', 'Phông nền', 'Sản phẩm', 'Văn bản', 'Sticker', 'Mẫu cảnh', 'Thiết kế', 'Kịch bản', 'Phiên live'):
        raise ValueError('Unsupported tab.')
    async with lock:
        active = await current_page()
        await active.get_by_role('button', name=name, exact=True).click()
        return await view()


@mcp.tool()
async def studio_save(personal_room_id: str = '') -> dict:
    """Save the owned Studio design and require a successful actual server PUT response."""
    async with lock:
        active = await current_page()
        async with active.expect_response(lambda response: '/api/studio-test/design?' in response.url and response.request.method == 'PUT', timeout=120000) as pending:
            await active.get_by_role('button', name='Lưu phòng & thiết kế', exact=True).click()
            chooser = active.locator('dialog select[data-room]')
            try:
                await chooser.wait_for(state='visible', timeout=3000)
            except Exception:
                pass
            else:
                if personal_room_id:
                    await chooser.select_option(value=personal_room_id)
                await active.locator('dialog [data-confirm]').click()
        response = await pending.value
        if not response.ok:
            raise ValueError('Server rejected the design save: HTTP ' + str(response.status))
        return {'saved': True, 'http_status': response.status}


@mcp.tool()
async def studio_start() -> dict:
    """Start an already rented, configured Studio lease. Idempotent when already live; never rents."""
    async with lock:
        active = await current_page()
        indicator = active.locator('#studio-live-indicator')
        if await indicator.get_attribute('data-state') == 'live':
            return {'state': 'live', 'already_running': True}
        button = active.get_by_role('button', name='Bắt đầu live', exact=True)
        await button.click()
        return {'state': 'preparing', 'instruction': 'Poll room_inspect and studio_output. Preparation can take minutes; do not click start again.'}


@mcp.tool()
async def studio_stop() -> dict:
    """Stop the current live broadcast only when requested. Does not release the paid room."""
    async with lock:
        active = await current_page()
        button = active.get_by_role('button', name='Dừng phiên live', exact=True)
        if await button.count() == 0:
            return {'state': 'unchanged', 'detail': 'No live stop button; inspect actual room state.'}
        await button.click()
        return {'state': 'stopping', 'billing': 'Room remains rented; stopping live does not stop machine billing.'}


async def copy_obs_link(active) -> str:
    """Capture only a fresh clipboard write produced by the actual OBS copy button."""
    button = active.get_by_role('button', name='Sao chép link OBS', exact=True)
    if await button.count() != 1 or not await button.is_enabled():
        raise ValueError('The OBS copy button is missing, ambiguous or disabled.')
    await active.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=origin)
    await active.evaluate("""() => {
      if (!navigator.clipboard?.writeText) throw Error('Clipboard API unavailable');
      const clipboard=navigator.clipboard;
      const original=clipboard.writeText;
      window.__aidolObsCopy={original, value:null, error:null};
      clipboard.writeText=async function(text){
        try {await original.call(clipboard,text); window.__aidolObsCopy.value=String(text);}
        catch(error){window.__aidolObsCopy.error=String(error);throw error;}
      };
    }""")
    try:
        await button.click()
        await active.wait_for_function("window.__aidolObsCopy?.value !== null || window.__aidolObsCopy?.error !== null", timeout=10000)
        captured = await active.evaluate('window.__aidolObsCopy.value')
        if not captured:
            raise ValueError('The OBS copy button did not write a link to the clipboard.')
        parsed = urlsplit(captured)
        if parsed.scheme != 'https' or parsed.netloc != 'room.genaidol.com' or not parsed.path.startswith('/studio-live/') or not parsed.path.endswith(('/player', '/rtc-player')) or not parsed.query:
            raise ValueError('The OBS copy button returned an unexpected URL; inspect the UI instead of substituting another link.')
        return captured
    finally:
        await active.evaluate("""() => {
          if(window.__aidolObsCopy){navigator.clipboard.writeText=window.__aidolObsCopy.original;delete window.__aidolObsCopy;}
        }""")


@mcp.tool()
async def studio_output() -> dict:
    """Click Sao chép link OBS and return its fresh clipboard payload. Never use the address bar or infer a URL. This does not certify OBS playback."""
    async with lock:
        active = await current_page()
        state = await active.locator('#studio-live-indicator').get_attribute('data-state')
        if state != 'live':
            return {'ready': False, 'state': state, 'detail': 'Live output is not ready.'}
        try:
            value = await copy_obs_link(active)
        except Exception as error:
            return {'ready': False, 'state': state, 'reason': 'obs_copy_failed', 'detail': type(error).__name__ + ': OBS copy button failed. Inspect the UI; do not substitute the browser address or an input URL.'}
        return {'ready': True, 'browser_source_url': value, 'link_source': 'obs_copy_button', 'playback_verified': False, 'private_link': True, 'obs': 'Paste this exact copied URL into OBS Browser Source, 720×1280 for portrait. Verify moving video and audio in OBS separately.'}


if __name__ == '__main__':
    mcp.run(transport='stdio')
