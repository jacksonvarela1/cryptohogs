#!/usr/bin/env python3
"""
Crypto Hogs · member resume book builder.

Pulls the opt-in members table through the token-gated get_resume_book RPC,
renders a branded HTML book, prints it to PDF with headless Chrome, and writes
the PDF OUTSIDE the repository. Member data is never published: the script
refuses to write anywhere inside the repo, even if asked to.

Usage
  python tools/resume-book.py              real data -> ~/Documents/CryptoHogs/resume-book/resume-book-YYYY-MM.pdf
  python tools/resume-book.py --demo       three obviously fake members, to check the layout without real data
  python tools/resume-book.py --png        also write a PNG preview of the first two pages (and of the PDF, if PyMuPDF is installed)
  python tools/resume-book.py --out DIR    write somewhere else (must still be outside the repo)
  python tools/resume-book.py --keep-html  keep the intermediate HTML next to the PDF

Needs Python 3.9+ and Google Chrome. The anon key is read from index.html, the reader token from
~/.claude/scheduled-tasks/cryptohogs-daily-build/resume-book-token.txt (set up by supabase/members.sql).
"""

import argparse
import base64
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home()
SB_URL = "https://umnizqaitlhulsxsasoz.supabase.co"
TOKEN_FILE = HOME / ".claude" / "scheduled-tasks" / "cryptohogs-daily-build" / "resume-book-token.txt"
DEFAULT_OUT = HOME / "Documents" / "CryptoHogs" / "resume-book"
COIN = REPO / "assets" / "coin-hero.jpg"
CHROME_CANDIDATES = [
    os.environ.get("CHROME"),
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
CARDS_PER_PAGE = 6
INTERESTS = ["Bitcoin", "DeFi", "Policy", "Engineering", "Trading and markets", "Quantum and cryptography", "Careers"]
CLUB_EMAIL = "uarkcryptohogs@gmail.com"
SITE = "jacksonvarela1.github.io/cryptohogs"


# ---------------------------------------------------------------- guards

def assert_outside_repo(path: Path, what: str) -> Path:
    """Refuse any path inside the repository. The book holds member data and is never published."""
    p = path.resolve()
    if p == REPO or REPO in p.parents:
        sys.exit(f"refusing to write {what} inside the repo ({p}). Member data is never published. Use --out with a folder outside {REPO}.")
    return p


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    for name in ("chrome", "google-chrome", "chromium", "chromium-browser"):
        w = shutil.which(name)
        if w:
            return w
    sys.exit("Google Chrome not found. Set the CHROME environment variable to the chrome executable.")


# ---------------------------------------------------------------- data

def anon_key() -> str:
    text = (REPO / "index.html").read_text(encoding="utf-8", errors="replace")
    m = re.search(r"sb_publishable_[A-Za-z0-9_-]+", text)
    if not m:
        sys.exit("could not find the Supabase anon key (sb_publishable_...) in index.html")
    return m.group(0)


def read_token() -> str:
    if not TOKEN_FILE.exists():
        sys.exit(f"token file missing: {TOKEN_FILE}\nRun supabase/members.sql first; it writes the same token there.")
    tok = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if len(tok) < 40:
        sys.exit(f"token in {TOKEN_FILE} looks wrong (too short)")
    return tok


def fetch_members(token: str, key: str) -> list:
    req = urllib.request.Request(
        SB_URL + "/rest/v1/rpc/get_resume_book",
        data=json.dumps({"p_token": token}).encode("utf-8"),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:400]
        sys.exit(f"Supabase said {e.code}: {body}\n(401/403 means the token does not match app_config.resume_book_token; 404 means members.sql has not been run)")
    except urllib.error.URLError as e:
        sys.exit(f"could not reach Supabase: {e.reason}")


def demo_members() -> list:
    return [
        {"full_name": "Sample Student One", "email": "not-a-real-student-1@uark.edu", "major": "Finance",
         "grad_term": "Spring 2028", "linkedin": "https://www.linkedin.com/in/example-one",
         "resume_url": "https://drive.google.com/example-one", "interests": ["Bitcoin", "Trading and markets", "Careers"]},
        {"full_name": "Sample Student Two", "email": "not-a-real-student-2@uark.edu", "major": "Computer Science",
         "grad_term": "Fall 2027", "linkedin": "https://www.linkedin.com/in/example-two",
         "resume_url": None, "interests": ["Engineering", "Quantum and cryptography", "DeFi"]},
        {"full_name": "Sample Student Three", "email": "not-a-real-student-3@uark.edu", "major": "Political Science",
         "grad_term": "Spring 2029", "linkedin": None,
         "resume_url": "https://example.com/sample-resume.pdf", "interests": ["Policy"]},
    ]


def term_key(term: str):
    m = re.match(r"^(Spring|Summer|Fall)\s+(\d{4})$", term or "")
    if not m:
        return (9999, 9, term or "")
    season = {"Spring": 0, "Summer": 1, "Fall": 2}[m.group(1)]
    return (int(m.group(2)), season, "")


def edition(today: dt.date) -> str:
    if today.month <= 5:
        return f"Spring {today.year}"
    if today.month <= 7:
        return f"Summer {today.year}"
    return f"Fall {today.year}"


# ---------------------------------------------------------------- render

CSS = """
:root{--ink:#0B0B0D;--ink-2:#131316;--cardinal:#9D2235;--hot:#C41230;--bronze:#C9A96A;--bronze-deep:#8f7546;
  --cream:#F4EFE4;--cream-dim:rgba(244,239,228,.62);--cream-faint:rgba(244,239,228,.42);
  --ink-dim:rgba(11,11,13,.66);--ink-faint:rgba(11,11,13,.46);--ink-line:rgba(11,11,13,.14);
  --font-d:'Space Grotesk',ui-sans-serif,system-ui,Arial,sans-serif;
  --font-s:'Instrument Serif',Georgia,serif;
  --font-m:'IBM Plex Mono',ui-monospace,Consolas,monospace;}
@page{size:Letter;margin:0}
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:#1a1a1d}
body{font-family:var(--font-d);color:var(--ink);letter-spacing:-.015em;-webkit-print-color-adjust:exact;print-color-adjust:exact;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.mono{font-family:var(--font-m);letter-spacing:.09em;text-transform:uppercase;font-size:8.5pt;font-weight:500}
.serif{font-family:var(--font-s);font-style:italic;font-weight:400;letter-spacing:0}
.page{width:8.5in;height:11in;overflow:hidden;position:relative;background:var(--cream);color:var(--ink);
  padding:.62in .68in .78in;page-break-after:always;break-after:page;margin:0 auto}
.page:last-child{page-break-after:auto;break-after:auto}
.foot{position:absolute;left:.68in;right:.68in;bottom:.42in;display:flex;justify-content:space-between;align-items:center;
  border-top:1px solid var(--ink-line);padding-top:8pt;color:var(--ink-faint)}
.page.dark{background:var(--ink);color:var(--cream)}
.page.dark .foot{border-top-color:rgba(244,239,228,.14);color:var(--cream-faint)}
/* cover */
.cover .top{display:flex;justify-content:space-between;align-items:center;color:var(--bronze)}
.cover .top .rso{color:var(--cream-faint)}
.cover .coinwrap{position:relative;width:3.1in;height:3.1in;margin:.62in auto .5in}
.cover .coinwrap::before{content:"";position:absolute;inset:-.7in;border-radius:50%;
  background:radial-gradient(circle,rgba(201,169,106,.22) 0%,rgba(157,34,53,.10) 38%,rgba(11,11,13,0) 68%)}
.cover .coinwrap img{position:relative;width:100%;height:100%;border-radius:50%;object-fit:cover;display:block;
  box-shadow:0 30px 60px rgba(0,0,0,.55)}
.cover h1{font-size:52pt;line-height:.98;font-weight:500;letter-spacing:-.035em;text-align:center}
.cover h1 .serif{color:var(--bronze)}
.cover .sub{text-align:center;color:var(--bronze);margin-top:16pt}
.cover .facts{display:grid;grid-template-columns:repeat(4,1fr);gap:0;margin-top:.55in;border-top:1px solid rgba(244,239,228,.14);border-bottom:1px solid rgba(244,239,228,.14)}
.cover .facts div{padding:14pt 12pt;border-left:1px solid rgba(244,239,228,.14)}
.cover .facts div:first-child{border-left:0;padding-left:0}
.cover .facts b{display:block;font-size:15pt;font-weight:500;letter-spacing:-.025em;line-height:1.15}
.cover .facts b .serif{color:var(--bronze)}
.cover .facts .lab{display:block;color:var(--cream-faint);margin-top:5pt}
.cover .confid{margin-top:.34in;color:var(--cream-dim);font-size:9.5pt;line-height:1.55;max-width:60ch}
.cover .confid b{color:var(--cream);font-weight:500}
/* intro */
.eyebrow{display:flex;align-items:center;gap:12pt;color:var(--bronze-deep);margin-bottom:16pt}
.eyebrow::after{content:"";height:1px;flex:1;background:var(--bronze-deep);opacity:.5}
.page.dark .eyebrow{color:var(--bronze)}
h2{font-size:26pt;font-weight:500;letter-spacing:-.03em;line-height:1.05;margin-bottom:14pt}
h2 .serif{color:var(--cardinal)}
.page.dark h2 .serif{color:var(--bronze)}
.intro p{color:var(--ink-dim);line-height:1.62;font-size:10.5pt;max-width:64ch;margin-bottom:9pt}
.intro p b{color:var(--ink);font-weight:500}
.glance{display:grid;grid-template-columns:1fr 1fr;gap:.32in;margin-top:.3in}
.glance h3{font-size:9pt;color:var(--bronze-deep);margin-bottom:10pt;font-weight:500}
.bar{display:grid;grid-template-columns:1.85in 1fr 28pt;align-items:center;gap:8pt;margin-bottom:7pt;font-size:9.5pt}
.bar span:first-child{color:var(--ink-dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar i{display:block;height:7pt;background:rgba(11,11,13,.08);border-radius:2px;overflow:hidden}
.bar i b{display:block;height:100%;background:var(--cardinal)}
.bar em{font-style:normal;text-align:right;font-family:var(--font-m);font-size:8.5pt;color:var(--ink-faint)}
.howto{margin-top:.28in;padding:14pt 16pt;border:1px solid var(--ink-line);border-radius:4px;background:rgba(11,11,13,.03)}
.howto .mono{color:var(--bronze-deep);display:block;margin-bottom:6pt}
.howto p{margin:0;font-size:10pt}
/* member pages */
.phead{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14pt;padding-bottom:9pt;border-bottom:1px solid var(--ink)}
.phead b{font-size:15pt;font-weight:500;letter-spacing:-.025em}
.phead b .serif{color:var(--cardinal)}
.phead span{color:var(--ink-faint)}
.cards{display:grid;grid-template-columns:1fr 1fr;grid-template-rows:repeat(3,1fr);gap:12pt;height:8.62in}
.card{border:1px solid var(--ink-line);border-radius:4px;padding:14pt 15pt 13pt;display:flex;flex-direction:column;background:#fbf9f3;
  min-height:0;overflow:hidden;position:relative}
.card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--cardinal)}
.card .nm{font-size:14.5pt;font-weight:500;letter-spacing:-.025em;line-height:1.1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.card .mj{color:var(--ink-dim);font-size:10pt;margin-top:4pt;line-height:1.35;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.card .term{display:inline-block;margin-top:8pt;color:var(--bronze-deep)}
.card .em{margin-top:6pt;font-family:var(--font-m);font-size:8.5pt;color:var(--ink-faint);letter-spacing:.02em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.card .chips{display:flex;flex-wrap:wrap;gap:5pt;margin-top:10pt;max-height:42pt;overflow:hidden}
.chip{font-family:var(--font-m);font-size:6.8pt;letter-spacing:.1em;text-transform:uppercase;padding:4pt 8pt;border-radius:100px;border:1px solid rgba(11,11,13,.24);color:var(--ink-dim);white-space:nowrap}
.card .links{margin-top:auto;padding-top:10pt;display:flex;gap:7pt;flex-wrap:wrap}
.card .links a{display:inline-flex;align-items:center;gap:6pt;font-size:9pt;font-weight:500;padding:6pt 10pt;border-radius:3px;
  border:1px solid var(--cardinal);color:var(--cardinal)}
.card .links a.cv{background:var(--cardinal);color:var(--cream)}
.card .links .none{font-size:9pt;color:var(--ink-faint);padding:6pt 0}
.empty{display:flex;align-items:center;justify-content:center;height:6in;color:var(--ink-faint);font-size:12pt;text-align:center;line-height:1.6}
.wm{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;pointer-events:none;
  font-size:110pt;font-weight:700;letter-spacing:.18em;color:rgba(157,34,53,.07);transform:rotate(-24deg)}
.page.dark .wm{color:rgba(244,239,228,.06)}
.back{display:flex;flex-direction:column;justify-content:flex-end;height:100%;padding-bottom:.4in}
.back h2{font-size:34pt;max-width:14ch}
.back p{color:var(--cream-dim);line-height:1.6;font-size:10.5pt;max-width:60ch;margin-bottom:9pt}
.back p b{color:var(--cream);font-weight:500}
.back .mono{color:var(--bronze)}
"""

FONTS = ("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700"
         "&family=Instrument+Serif:ital@0;1&family=IBM+Plex+Mono:wght@400;500&display=swap")


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def safe_link(url) -> str:
    """Only http(s) links get rendered as links."""
    if not url:
        return ""
    u = str(url).strip()
    return u if re.match(r"^https?://[^\s\"'<>]+$", u) else ""


def short_host(url: str) -> str:
    m = re.match(r"^https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else url


def render(members: list, demo: bool, today: dt.date) -> str:
    ed = edition(today)
    n = len(members)
    coin_b64 = base64.b64encode(COIN.read_bytes()).decode("ascii")
    members = sorted(members, key=lambda m: (term_key(m.get("grad_term")), (m.get("full_name") or "").lower()))
    member_pages = [members[i:i + CARDS_PER_PAGE] for i in range(0, n, CARDS_PER_PAGE)] or [[]]
    total = 3 + len(member_pages)   # cover, intro, member pages, back
    wm = '<div class="wm" aria-hidden="true">SAMPLE</div>' if demo else ""
    label = "SAMPLE DATA · NOT REAL STUDENTS" if demo else "Confidential · sponsors only"

    def foot(i: int) -> str:
        return (f'<div class="foot mono"><span>Crypto Hogs · Member resume book · {esc(ed)}</span>'
                f'<span>{label} · {i} / {total}</span></div>')

    # ---- cover
    out = [f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Crypto Hogs · Member resume book · {esc(ed)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet"><style>{CSS}</style></head><body>
<section class="page dark cover">{wm}
  <div class="top mono"><span>Crypto Hogs · University of Arkansas</span><span class="rso">Registered student organization</span></div>
  <div class="coinwrap"><img src="data:image/jpeg;base64,{coin_b64}" alt="The Crypto Hogs coin"></div>
  <h1>Member <span class="serif">resume book.</span></h1>
  <p class="sub mono">{esc(ed)} edition · {n} member{"" if n == 1 else "s"} · prepared for club sponsors</p>
  <div class="facts">
    <div><b>150<span class="serif">+</span></b><span class="mono lab">members in year one</span></div>
    <div><b>Spring <span class="serif">2026</span></b><span class="mono lab">founded</span></div>
    <div><b>Tue <span class="serif">5:30 PM</span></b><span class="mono lab">weekly · 5:30 to 7:00 CT</span></div>
    <div><b>Free, <span class="serif">open</span></b><span class="mono lab">to all UA students</span></div>
  </div>
  <p class="confid"><b>Shared in confidence.</b> Every student in this book opted in and agreed to be contacted by Crypto Hogs
  sponsors about internships and jobs. Please keep it inside your recruiting team, do not repost or forward it, and use
  the links rather than copying the data elsewhere. Questions and removals: {CLUB_EMAIL}.</p>
  {foot(1)}
</section>"""]

    # ---- intro / at a glance
    by_term, by_int = {}, {}
    for m in members:
        by_term[m.get("grad_term") or "Unknown"] = by_term.get(m.get("grad_term") or "Unknown", 0) + 1
        for it in (m.get("interests") or []):
            by_int[it] = by_int.get(it, 0) + 1
    mx_t = max(by_term.values(), default=1)
    mx_i = max(by_int.values(), default=1)

    def bars(d: dict, mx: int, order=None) -> str:
        keys = order if order else sorted(d, key=term_key)
        rows = []
        for k in keys:
            v = d.get(k, 0)
            if order is None and v == 0:
                continue
            rows.append(f'<div class="bar"><span>{esc(k)}</span><i><b style="width:{(v / mx) * 100:.0f}%"></b></i><em>{v}</em></div>')
        return "".join(rows) or '<div class="bar"><span>None yet</span><i></i><em>0</em></div>'

    out.append(f"""<section class="page intro">{wm}
  <div class="eyebrow mono">About this book</div>
  <h2>Who is in here, <span class="serif">and how to use it.</span></h2>
  <p>Crypto Hogs is the cryptocurrency club at the University of Arkansas: <b>150+ members</b> in its first year, founded in
  spring 2026, meeting Tuesdays 5:30 to 7:00 PM CT. Every event is free and open to all UA students, and every member is
  here because they chose to show up on a Tuesday evening to learn about money, markets, and the technology underneath them.</p>
  <p>This book is the part of a Partner or Founding sponsorship that pays back first. Each card is a member who <b>asked to be
  seen</b>: their major, expected graduation, the topics they care about, and links they control to their LinkedIn and resume.
  We rebuild it at the start of each semester, so the links are always the freshest copy the student has.</p>
  <p>Please reach out to students directly through the links on their card, mention Crypto Hogs so they know where you found
  them, and copy {CLUB_EMAIL} if you would like an introduction or a table at a Tuesday meeting.</p>
  <div class="glance">
    <div><h3 class="mono">By expected graduation</h3>{bars(by_term, mx_t)}</div>
    <div><h3 class="mono">By interest</h3>{bars(by_int, mx_i, INTERESTS)}</div>
  </div>
  <div class="howto"><span class="mono">Reading a card</span>
  <p>Name and major up top, graduation term in bronze, interests as chips, and the two buttons at the bottom open the student's
  LinkedIn and resume. A card without a resume button means the student has not shared one yet; their LinkedIn is the way in.</p></div>
  {foot(2)}
</section>""")

    # ---- member pages
    pg = 3
    for i, chunk in enumerate(member_pages):
        cards = []
        for m in chunk:
            li = safe_link(m.get("linkedin"))
            cv = safe_link(m.get("resume_url"))
            chips = "".join(f'<span class="chip">{esc(x)}</span>' for x in (m.get("interests") or []) if x)
            links = []
            if cv:
                links.append(f'<a class="cv" href="{esc(cv)}">Resume <span aria-hidden="true">&#8599;</span></a>')
            if li:
                links.append(f'<a href="{esc(li)}">LinkedIn <span aria-hidden="true">&#8599;</span></a>')
            if not links:
                links.append(f'<span class="none">No links yet. Reach out at {esc(m.get("email"))}.</span>')
            cards.append(f"""<div class="card">
        <div class="nm">{esc(m.get("full_name"))}</div>
        <div class="mj">{esc(m.get("major"))}</div>
        <span class="term mono">Class of {esc(m.get("grad_term"))}</span>
        <div class="em">{esc(m.get("email"))}</div>
        <div class="chips">{chips or '<span class="chip" style="opacity:.55">No interests listed</span>'}</div>
        <div class="links">{"".join(links)}</div>
      </div>""")
        body = f'<div class="cards">{"".join(cards)}</div>' if cards else \
            '<div class="empty">No members have joined the book yet.<br>Send students to the Join page and rebuild.</div>'
        out.append(f"""<section class="page">{wm}
  <div class="phead"><b>Members <span class="serif">{i + 1} of {len(member_pages)}.</span></b><span class="mono">{len(chunk)} on this page · by graduation, then name</span></div>
  {body}
  {foot(pg)}
</section>""")
        pg += 1

    # ---- back page
    out.append(f"""<section class="page dark">{wm}
  <div class="back">
    <span class="mono">Crypto Hogs · {SITE}</span>
    <h2 style="margin-top:14pt">Thank you for <span class="serif">backing the room.</span></h2>
    <p>Sponsor money is what turns a group chat into speakers, workshops, and a room full of students every Tuesday.
    <b>This book is our thank-you</b>, refreshed every semester for as long as you are with us.</p>
    <p>Corrections, removals, or a student who would like to be introduced: <b>{CLUB_EMAIL}</b>.
    Members may leave the book at any time by emailing that address, and we ask that you delete any copy of a card
    once we tell you it has been withdrawn.</p>
    <p style="font-size:9pt;color:rgba(244,239,228,.42)">Crypto Hogs is a registered student organization at the University of Arkansas.
    It is not an official unit of the university and does not speak for it. Nothing in this book is financial advice.
    Built {today.isoformat()}.</p>
  </div>
  {foot(total)}
</section>
</body></html>""")
    return "\n".join(out)


# ---------------------------------------------------------------- chrome

def run_chrome(chrome: str, url: str, *extra: str) -> None:
    prof = Path(tempfile.mkdtemp(prefix="ch-resume-book-"))
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
           "--force-device-scale-factor=1", f"--user-data-dir={prof}", "--virtual-time-budget=15000",
           *extra, url]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    except subprocess.CalledProcessError as e:
        sys.exit(f"chrome failed ({e.returncode}) running: {' '.join(cmd[:4])} ...")
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def pdf_pages(pdf: Path) -> int:
    try:
        from pypdf import PdfReader  # type: ignore
        return len(PdfReader(str(pdf)).pages)
    except Exception:
        return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def pdf_previews(pdf: Path, out_dir: Path, stem: str, pages: int = 2) -> list:
    """Rasterise the first pages of the PDF itself, when PyMuPDF is available."""
    try:
        import pymupdf as fitz  # type: ignore
    except Exception:
        try:
            import fitz  # type: ignore
        except Exception:
            return []
    made = []
    with fitz.open(str(pdf)) as doc:
        for i in range(min(pages, doc.page_count)):
            png = out_dir / f"{stem}-pdf-p{i + 1}.png"
            doc[i].get_pixmap(dpi=110).save(str(png))
            made.append(png)
    return made


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description="Build the Crypto Hogs member resume book PDF (outside the repo).")
    ap.add_argument("--demo", action="store_true", help="render three fake sample members instead of real data")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help=f"output folder, must be outside the repo (default {DEFAULT_OUT})")
    ap.add_argument("--png", action="store_true", help="also write PNG previews of the first two pages")
    ap.add_argument("--keep-html", action="store_true", help="keep the intermediate HTML next to the PDF")
    args = ap.parse_args()

    today = dt.date.today()
    out_dir = assert_outside_repo(Path(args.out), "the book")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = "resume-book-DEMO" if args.demo else f"resume-book-{today:%Y-%m}"
    pdf = assert_outside_repo(out_dir / f"{stem}.pdf", "the PDF")
    html_path = assert_outside_repo(out_dir / f"{stem}.html", "the HTML")

    if args.demo:
        members = demo_members()
        print("demo mode: rendering 3 sample members, no network")
    else:
        members = fetch_members(read_token(), anon_key())
        print(f"fetched {len(members)} member{'' if len(members) == 1 else 's'} from Supabase")

    html_path.write_text(render(members, args.demo, today), encoding="utf-8")
    chrome = find_chrome()
    url = html_path.as_uri()
    run_chrome(chrome, url, f"--print-to-pdf={pdf}", "--no-pdf-header-footer")
    if not pdf.exists() or pdf.stat().st_size < 1000:
        sys.exit("chrome did not produce a PDF")
    print(f"wrote {pdf}  ({pdf.stat().st_size // 1024} KB, {pdf_pages(pdf)} pages)")

    if args.png:
        shot = out_dir / f"{stem}-preview.png"
        run_chrome(chrome, url, f"--screenshot={shot}", "--window-size=816,2112")
        print(f"wrote {shot}  (HTML render of the first two pages)")
        for p in pdf_previews(pdf, out_dir, stem):
            print(f"wrote {p}  (rasterised from the PDF)")

    if args.keep_html:
        print(f"kept {html_path}")
    else:
        html_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
