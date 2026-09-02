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

Four places have to move together:

1. `events.html`, the rows inside `<div class="sched" id="sched">`.
2. `index.html`, the shorter schedule block in the events section (same rows, less detail).
3. `events.html`, the `application/ld+json` block in `<head>`. It holds one `Event` object per confirmed speaker night. Google reads this. Keep dates in ISO form with the `-05:00` offset, `isAccessibleForFree` true, and `eventAttendanceMode` matching whether the session is in person or virtual.
4. `sitemap.xml`, bump `<lastmod>` for any page you edited.

Rows dated in the past dim themselves automatically and the homepage "Next block" line advances on its own, so nothing needs editing week to week. The date logic assumes the year `2026`. When the spring 2027 schedule goes up, change the literal in the schedule script at the bottom of `events.html`, and on the homepage change `data-year="2026"` to `data-year="2027"` on the `<div class="sched reveal">` element (its script reads that attribute). Do both in the same commit.

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
