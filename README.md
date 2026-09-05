# Crypto Hogs website

Live: https://jacksonvarela1.github.io/cryptohogs/
Hosting: GitHub Pages, `main` branch, repo root. Every push to `main` deploys in about a minute.

## Layout

| File | What it is |
|---|---|
| `index.html` | Homepage. Self-contained: its CSS and JS are inline. Runs the 3D coin (three.js), headline animations (GSAP), live prices, the halving clock, and the FPS watchdog that drops to a lighter mode on slow devices. |
| `team.html`, `events.html`, `sponsors.html` | Subpages. They share `assets/site.css` and `assets/site.js` plus a small page-specific `<style>` block in their own `<head>`. |
| `404.html` | Branded not-found page. Its links use absolute `/cryptohogs/` paths because GitHub Pages serves the site under that subpath. Change them if the site moves to a custom domain at the root. |
| `assets/vendor/` | three.js 0.160, GSAP 3.12.5, ScrollTrigger. Self-hosted so the Content Security Policy can stay strict. Do not swap these for CDN copies. |
| `assets/coin-tex/` | The coin's PBR maps. Color maps are JPEG, detail maps (normal, roughness, metalness, AO) are WebP. The loader builds the filenames, so renaming one breaks the coin silently. |
| `assets/web/` | Officer photos. Each has an 800px original and a `-560.jpg` variant for small screens. Add both when adding a person. |
| `assets/cryptohogs-sponsorship.pdf` | The public sponsorship deck. See the PDF rule below. |
| `sitemap.xml`, `robots.txt` | Search plumbing. |

## Changing the schedule or a speaker

One file, one command, one commit:

1. Edit `assets/schedule.json`. Every row of the lineup lives there and nowhere else.
2. Run `python tools/build-schedule.py` from the repo root (standard library only, Python 3.9+).
3. Commit whatever changed: `schedule.json`, `index.html`, `events.html`, `assets/events/*.ics`, `sitemap.xml`.

The script rewrites only the text between `<!-- schedule:NAME:start -->` and `<!-- schedule:NAME:end -->` comment markers. Never hand-edit inside a marker pair (the next run overwrites it) and never move or rename the markers (the script stops with an error if a pair is missing). Running it twice in a row changes nothing.

| Region | Page | What it holds |
|---|---|---|
| `rows` | `events.html`, `index.html` | The whole `.sched` lineup block, including its `data-year` attribute. |
| `breaks` | `events.html`, `index.html` | The "No meeting ..." chips. The "Schedule may shift" chip after them is hand-written. |
| `jsonld` | `events.html` `<head>` | One schema.org `Event` per confirmed row with a slug. Google reads this. |
| `next` | `index.html` hero | The no-JS fallback for the "Next block" line: the first row on or after the day you run the script. |

Outside the markers it also writes `assets/events/<date>-<slug>.ics` for every confirmed row that has a slug (CRLF and 75-octet folding per RFC 5545; a file whose event did not change keeps its `DTSTAMP`, and .ics files that no longer match a row are deleted), builds the "Add to calendar" and Google Calendar links in those rows, and bumps `<lastmod>` in `sitemap.xml` for a page only when that page's generated content changed. The "Your first Tuesday" block on `events.html` reuses the `.sched` look but is hand-written and untouched.

Row fields in `schedule.json`:

- `date` (YYYY-MM-DD) on every row. All rows must fall in one calendar year; that year becomes `data-year`, which both page scripts read for the past-row dimming and the homepage countdown. A note is printed if a date is not a Tuesday.
- `kind`: `speaker`, `general`, `break` or `finale`. `status`: `confirmed`, `tba`, `done` or `break`. Break rows use `break` for both and need only `date` and `title` (for example "Fall Break"); they become chips, not rows.
- `title` is the row headline and the JSON-LD name. `small` is the one-line detail under it on `events.html`; `small_home` is the shorter homepage version and defaults to `small`. Write plain text (`Q&A`, `&`); the script escapes it.
- Confirmed or done speaker rows also need `speaker`, `org` and `format` (`virtual` or `in-person`). To get a calendar file, the calendar links and a JSON-LD entry, a confirmed row needs `slug` (a-z, 0-9, hyphens; part of the .ics filename), `short` (the calendar title, prefixed "Crypto Hogs: "), `description` (JSON-LD) and `calendar_description` (the .ics body and the Google link).
- Optional: `role` (jobTitle in JSON-LD), `location` (overrides "Virtual. Room announced in the club GroupMe." or "University of Arkansas, Fayetteville, AR"), `hero` (wording for the homepage "Next block" fallback, defaults to the title).
- Chips are derived: confirmed shows "Confirmed", `tba` shows "Speaker TBA", `done` shows "Done" and pre-dims the row, `finale` shows "Last meeting".

Meeting time comes from the top-level `start`, `end` and `timezone` (17:30 to 19:00 America/Chicago). The script works out the UTC offset per date, so rows after the clocks change in November correctly get `-06:00`. No em dashes anywhere in the file; the script refuses to run if it finds one.

Rows dated in the past dim themselves automatically and the homepage "Next block" line advances on its own, so nothing needs editing week to week. When the spring schedule goes up, replace the rows in `schedule.json` and run the script; `data-year` follows the dates.

Only name a speaker once they are confirmed. Every event must stay free and open to all UA students, and talks are framed by topic, never as a company showcase. Those two rules come from ASG funding requirements.

## Changing officers

The homepage cards come from the `OFFICERS` array near the bottom of `index.html`. Each entry links to `team.html#slug`, so a new person needs a matching `<div class="profile reveal" id="slug">` block on the team page. Bios follow the same shape for everyone: one paragraph of background, one paragraph connecting it to their club role, and only facts that can be verified from a source the person controls.

## The PDF rule

Before hosting any document from the shared Drive, strip personal phone numbers, personal emails, and the club's university account number. The public deck's footer should carry only the club address, `uarkcryptohogs@gmail.com`. The Drive original is for sponsors we are already talking to. The public copy is for anyone on the internet.

## House style

- No em dashes anywhere in copy. Use a period, a comma, a colon, or ` · `.
- Copy voice: plain, confident, a little playful. "For the curious, not the experts."
- Colors and type are fixed: ink `#0B0B0D`, cream `#F4EFE4`, cardinal `#9D2235` / `#C41230`, bronze `#C9A96A`; Space Grotesk, Instrument Serif italic for accents, IBM Plex Mono for labels.
- Keep the Content Security Policy `<meta>` on every page. It is the same string on all four main pages. Adding a new external script or image host means adding it there too.

## Checking a change before you push

Serve the folder locally and open it in a browser:

```bash
python -m http.server 4173
```

Useful URL flags, all local-only test hooks: `?static` turns off motion and shows every section in its final state, `?motion` forces motion on even if the OS prefers reduced motion, and `?dbg` prints the watchdog's frame timings to the console.

Things worth a look before pushing: the page at phone width (390px), the browser console for errors, and a search of your diff for the em dash character.
