"""Accesso al sito web di Vadoo AI con l'account dell'utente (login OTP via email)
e generazione/scaricamento immagini come dal sito. Profilo browser persistente."""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright

STUDIO = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(STUDIO, ".vadoo_profile")   # sessione di login (NON va su git)
CHROME = os.environ.get("PW_CHROMIUM", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
SITEKEY = "6Lc0jcQqAAAAANodWjnV_8cX4DW4yxrrD9xYjgcT"


async def open_ctx(p, headless=True):
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    ctx = await p.chromium.launch_persistent_context(
        PROFILE, headless=headless, executable_path=CHROME if os.path.exists(CHROME) else None,
        proxy={"server": proxy} if proxy else None,
        args=["--disable-blink-features=AutomationControlled"],
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"),
        viewport={"width": 1366, "height": 900}, locale="en-US")
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    return ctx, page


async def api(page, method, path, body=None):
    return await page.evaluate("""async ([m, u, b]) => {
        const r = await fetch(u, {method: m, credentials: 'include',
            headers: b ? {'Content-Type': 'application/json'} : {}, body: b ? JSON.stringify(b) : undefined});
        const t = await r.text(); return {status: r.status, text: t};
    }""", [method, path, body])


async def send_otp(email):
    async with async_playwright() as p:
        ctx, page = await open_ctx(p)
        await page.goto("https://ai.vadoo.tv/login", wait_until="networkidle", timeout=90000)
        token = None
        for _ in range(20):
            await page.wait_for_timeout(1500)
            try:
                token = await page.evaluate("""(k) => new Promise((res, rej) => {
                    if (!window.grecaptcha) return rej('no grecaptcha');
                    grecaptcha.ready(() => grecaptcha.execute(k, {action: 'submit'}).then(res, rej)); })""", SITEKEY)
                if token:
                    break
            except Exception as exc:
                print("captcha wait:", str(exc)[:120])
        print("token len", len(token or ""))
        r = await api(page, "POST", "/api/login", {"email": email, "token": token})
        print("send_otp:", r["status"], r["text"][:300])
        await ctx.close()


async def verify(email, code):
    async with async_playwright() as p:
        ctx, page = await open_ctx(p)
        await page.goto("https://ai.vadoo.tv/login", wait_until="domcontentloaded", timeout=90000)
        r = await api(page, "POST", "/api/verify_code", {"email": email, "code": code, "appsumo_code": None, "discounted": True})
        print("verify:", r["status"], r["text"][:300])
        r = await api(page, "GET", "/api/isLoggedIn")
        print("isLoggedIn:", r["text"][:200])
        await ctx.close()


async def status():
    async with async_playwright() as p:
        ctx, page = await open_ctx(p)
        await page.goto("https://ai.vadoo.tv/ai-image", wait_until="domcontentloaded", timeout=90000)
        for path in ("/api/isLoggedIn", "/api/get_server_details"):
            r = await api(page, "GET", path)
            print(path, r["status"], r["text"][:3000])
        await ctx.close()


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "send":
        asyncio.run(send_otp(sys.argv[2]))
    elif cmd == "verify":
        asyncio.run(verify(sys.argv[2], sys.argv[3]))
    elif cmd == "status":
        asyncio.run(status())


def download(url, fn, tries=30):
    import requests
    for _ in range(tries):
        r = requests.get(url, timeout=120)
        if r.status_code == 200 and r.content[:3] in (b"\xff\xd8\xff", b"\x89PN", b"RIF"):
            open(fn, "wb").write(r.content)
            return True
        time.sleep(5)
    return False


async def refetch(task_id, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    async with async_playwright() as p:
        ctx, page = await open_ctx(p)
        await page.goto("https://ai.vadoo.tv/ai-image", wait_until="domcontentloaded", timeout=90000)
        s = await api(page, "POST", "/api/get_flux_image_status", {"task_id": task_id})
        await ctx.close()
    sd = json.loads(s["text"])
    for n, img in enumerate((sd.get("results") or {}).get("images", []), 1):
        url = img.get("url") or img.get("image_url")
        fn = os.path.join(out_dir, f"{name}_{n}.jpg")
        print(download(url, fn), fn, url)


def payload(model, prompt, ratio="9:16", w=720, h=1280, num=1, images=None):
    return {"models": [model], "images_list": images or [], "google_search": False, "customPrompt": prompt,
            "imageSizes": {"ratio": ratio, "width": w, "height": h}, "numImages": num, "imgStyle": None,
            "imgLighting": {"name": None, "description": None}, "imgCamera": {"name": None, "description": None},
            "allowModify": False, "effect": None, "loraList": [], "fluxLoraList": [], "guidanceScale": 3.5,
            "numInferSteps": 28, "imageQuality": "medium", "renderSpeed": "Balanced", "multiSelection": False,
            "hidreamType": "hidream_dev", "stylization": 1, "weirdness": 1, "variety": 5, "omniWeight": 100,
            "higgsfieldStyle": "General", "strength": 0.5, "resolution": "1k", "lora_weight": 1, "loraScale": 1}


async def credits(page):
    r = await api(page, "GET", "/api/get_server_details")
    try:
        return json.loads(r["text"])["user_subscription_details"].get("remaining_credits")
    except Exception:
        import re
        m = re.search(r'"remaining_credits":\s*(\d+)', r["text"])
        return int(m.group(1)) if m else None


async def _run_job(page, job, out_dir):
    body = payload(job["model"], job["prompt"], num=job.get("num", 1), images=job.get("images"))
    r = await api(page, "POST", "/api/flux_image_generation", body)
    print(job["name"], "submit:", r["status"], r["text"][:300], flush=True)
    if r["status"] != 200:
        return
    d = json.loads(r["text"])
    tids = [x["task_id"] for x in d["results"]] if isinstance(d.get("results"), list) else [d["task_id"]]
    n = 0
    for tid in tids:
        t0 = time.time()
        while time.time() - t0 < 600:
            await page.wait_for_timeout(4000)
            s = await api(page, "POST", "/api/get_flux_image_status", {"task_id": tid})
            sd = json.loads(s["text"]) if s["text"].startswith("{") else {}
            st = sd.get("status")
            if st == "COMPLETED":
                for img in (sd.get("results") or {}).get("images", []):
                    url = img.get("url") or img.get("image_url")
                    if not url:
                        print("  image err:", img, flush=True)
                        continue
                    n += 1
                    ext = os.path.splitext(url.split("?")[0])[1] or ".png"
                    fn = os.path.join(out_dir, f"{job['name']}_{n}{ext}")
                    ok = await asyncio.to_thread(download, url, fn)
                    print("  saved" if ok else "  NOT READY", fn, url, flush=True)
                break
            if st in ("FAILED", "failed", "ERROR"):
                print("  failed:", job["name"], s["text"][:300], flush=True)
                break
        else:
            print("  timeout", job["name"], tid, flush=True)


async def generate(jobs_file, out_dir, conc=2):
    """jobs_file: JSON [{"name":..., "model":..., "prompt":..., "num":1, "images":[urls]}]
    conc = immagini generate in parallelo (il piano Starter di Vadoo ne permette 2)."""
    jobs = json.load(open(jobs_file))
    os.makedirs(out_dir, exist_ok=True)
    async with async_playwright() as p:
        ctx, page = await open_ctx(p)
        await page.goto("https://ai.vadoo.tv/ai-image", wait_until="domcontentloaded", timeout=90000)
        print("credits before:", await credits(page), flush=True)
        queue = list(jobs)

        async def worker():
            while queue:
                job = queue.pop(0)
                try:
                    await _run_job(page, job, out_dir)
                except Exception as exc:
                    print("  error:", job["name"], exc, flush=True)

        await asyncio.gather(*[worker() for _ in range(conc)])
        print("credits after:", await credits(page), flush=True)
        await ctx.close()


if __name__ == "__main__" and sys.argv[1] == "gen":
    asyncio.run(generate(sys.argv[2], sys.argv[3]))


async def upload(path):
    import base64
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    name = os.path.basename(path)
    async with async_playwright() as p:
        ctx, page = await open_ctx(p)
        await page.goto("https://ai.vadoo.tv/ai-image", wait_until="domcontentloaded", timeout=90000)
        res = await page.evaluate("""async ([name, b64]) => {
            const r = await fetch('/api/get_ai_media_upload_url?filename=' + encodeURIComponent(name), {credentials: 'include'});
            const d = await r.json();
            const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
            const fd = new FormData();
            Object.entries(d.fields).forEach(([k, v]) => fd.append(k, v));
            fd.append('file', new Blob([bin], {type: 'image/png'}), name);
            const u = await fetch(d.url, {method: 'POST', body: fd});
            const key = d.fields.key;
            const s = await fetch('/api/save_uploaded_ai_media', {method: 'POST', credentials: 'include',
                headers: {'Content-Type': 'application/json'}, body: JSON.stringify({url: key})});
            return {upload: u.status, key, saved: await s.text()};
        }""", [name, b64])
        print(json.dumps(res)[:1500])
        await ctx.close()


if __name__ == "__main__" and sys.argv[1] == "refetch":
    asyncio.run(refetch(sys.argv[2], sys.argv[3], sys.argv[4]))

if __name__ == "__main__" and sys.argv[1] == "upload":
    asyncio.run(upload(sys.argv[2]))
