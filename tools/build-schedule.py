#!/usr/bin/env python3
"""Regenerate every schedule-derived part of the site from assets/schedule.json.

Run from anywhere:  python tools/build-schedule.py

What it rewrites (and nothing else):
  events.html   <!-- schedule:rows -->, <!-- schedule:breaks -->, <!-- schedule:jsonld -->
  index.html    <!-- schedule:rows -->, <!-- schedule:breaks -->, <!-- schedule:next -->
  assets/events/<date>-<slug>.ics   one per confirmed row that has a slug (stale ones removed)
  sitemap.xml   <lastmod> for index.html and events.html, only when that page changed

Only the text between a region's start and end markers is replaced, so everything
around the markers (classes, ids, the "Your first Tuesday" block, page scripts) is
left alone. Line endings of each file are preserved (index.html is CRLF).
Standard library only, Python 3.9+.
"""
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "schedule.json"
ICS_DIR = ROOT / "assets" / "events"
SITEMAP = ROOT / "sitemap.xml"

KINDS = {"speaker", "general", "break", "finale"}
STATUSES = {"confirmed", "tba", "done", "break"}
FORMATS = {"virtual", "in-person"}
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PRODID = "-//Crypto Hogs//UARK//EN"
UID_DOMAIN = "cryptohogs.uark"
PLACE = {"@type": "Place", "name": "University of Arkansas",
         "address": {"@type": "PostalAddress", "addressLocality": "Fayetteville",
                     "addressRegion": "AR", "addressCountry": "US"}}
ORGANIZER = {"@type": "Organization", "name": "Crypto Hogs"}
VIRTUAL_LOCATION_TEXT = "Virtual. Room announced in the club GroupMe."
CAMPUS_LOCATION_TEXT = "University of Arkansas, Fayetteville, AR"
DOT = "\u00b7"


def fail(msg):
    sys.stderr.write("build-schedule: " + msg + "\n")
    sys.exit(1)


# ---------------------------------------------------------------- time zone
class _USCentral(dt.tzinfo):
    """Fallback for boxes without tzdata: US rules since 2007, Central only."""

    def _dst(self, t):
        if t is None:
            return False
        y = t.year
        mar8 = dt.datetime(y, 3, 8)
        nov1 = dt.datetime(y, 11, 1)
        mar = mar8 + dt.timedelta(days=(6 - mar8.weekday()) % 7)   # second Sunday of March
        nov = nov1 + dt.timedelta(days=(6 - nov1.weekday()) % 7)   # first Sunday of November
        naive = t.replace(tzinfo=None)
        return mar.replace(hour=2) <= naive < nov.replace(hour=2)

    def utcoffset(self, t):
        return dt.timedelta(hours=-5 if self._dst(t) else -6)

    def dst(self, t):
        return dt.timedelta(hours=1 if self._dst(t) else 0)

    def tzname(self, t):
        return "CDT" if self._dst(t) else "CST"


def get_tz(name):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        if name != "America/Chicago":
            fail("no tz database on this machine and the fallback only knows America/Chicago")
        return _USCentral()


# ---------------------------------------------------------------- load + validate
def has_calendar(r):
    return r.get("status") == "confirmed" and bool(r.get("slug"))


def load():
    raw = SRC.read_bytes().decode("utf-8")
    if "\u2014" in raw:
        fail("schedule.json contains an em dash (U+2014); house style forbids it")
    data = json.loads(raw)
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        fail("schedule.json needs a non-empty 'rows' list")
    for key in ("timezone", "start", "end", "site"):
        if not data.get(key):
            fail("schedule.json is missing '%s'" % key)
    seen = set()
    for r in rows:
        where = "row %s" % r.get("date", "?")
        try:
            r["_date"] = dt.date.fromisoformat(r.get("date", ""))
        except ValueError:
            fail(where + ": 'date' must be YYYY-MM-DD")
        if r["_date"] in seen:
            fail(where + ": duplicate date")
        seen.add(r["_date"])
        if r.get("kind") not in KINDS:
            fail(where + ": 'kind' must be one of " + ", ".join(sorted(KINDS)))
        if r.get("status") not in STATUSES:
            fail(where + ": 'status' must be one of " + ", ".join(sorted(STATUSES)))
        if (r["kind"] == "break") != (r["status"] == "break"):
            fail(where + ": kind 'break' and status 'break' go together")
        if not r.get("title"):
            fail(where + ": 'title' is required")
        if r["kind"] != "break" and not r.get("small"):
            fail(where + ": 'small' (the one-line detail under the title) is required")
        if r["kind"] in ("speaker", "general") and r["status"] in ("confirmed", "done"):
            for key in ("speaker", "org", "format"):
                if not r.get(key):
                    fail(where + ": confirmed speaker rows need '%s'" % key)
        if r.get("format") and r["format"] not in FORMATS:
            fail(where + ": 'format' must be 'virtual' or 'in-person'")
        if has_calendar(r):
            for key in ("description", "short", "calendar_description", "format"):
                if not r.get(key):
                    fail(where + ": rows with a slug need '%s'" % key)
            if not re.fullmatch(r"[a-z0-9-]+", r["slug"]):
                fail(where + ": 'slug' may only use a-z, 0-9 and hyphens")
        if r["_date"].weekday() != 1:
            sys.stderr.write("build-schedule: note, %s is a %s, not a Tuesday\n"
                             % (r["date"], DAYS[r["_date"].weekday()].title()))
    rows.sort(key=lambda r: r["_date"])
    years = {r["_date"].year for r in rows}
    if len(years) > 1:
        fail("rows span more than one calendar year; the page scripts read a single data-year")
    data["_year"] = years.pop()
    return data, rows


# ---------------------------------------------------------------- formatting helpers
def esc(s):
    return html.escape(s, quote=False)


def date_label(d):
    return "%s %s %s %d" % (DAYS[d.weekday()], DOT, MONTHS[d.month - 1].upper(), d.day)


def month_day(d):
    return "%s %d" % (MONTHS[d.month - 1], d.day)


def local_time(d, hhmm, tz):
    h, m = (int(x) for x in hhmm.split(":"))
    return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=tz)


def utc_stamp(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def location_text(r):
    if r.get("location"):
        return r["location"]
    return VIRTUAL_LOCATION_TEXT if r["format"] == "virtual" else CAMPUS_LOCATION_TEXT


def ics_name(r):
    return "%s-%s.ics" % (r["date"], r["slug"])


def chip(r):
    if r["status"] == "done":
        return "chip", "Done"
    if r["status"] == "tba":
        return "chip tba", "Speaker TBA"
    if r["kind"] == "finale":
        return "chip", "Last meeting"
    return "chip hot", "Confirmed"


def gcal_link(r, start, end):
    q = [("action", "TEMPLATE"),
         ("text", "Crypto Hogs: " + r["short"]),
         ("dates", "%s/%s" % (utc_stamp(start), utc_stamp(end))),
         ("details", r["calendar_description"]),
         ("location", location_text(r))]
    return "https://calendar.google.com/calendar/render?" + "&".join(k + "=" + quote_plus(v) for k, v in q)


# ---------------------------------------------------------------- generated regions
def rows_region(rows, data, page, tz):
    ev = page == "events.html"
    if ev:
        out = ['<div class="sched" id="sched" data-year="%d">' % data["_year"]]
    else:
        out = ['<div class="sched reveal" data-year="%d">' % data["_year"]]
    for r in rows:
        if r["kind"] == "break":
            continue
        cls = "row reveal" if ev else "row"
        if r["status"] == "done":
            cls += " past"
        small = r["small"] if ev else r.get("small_home", r["small"])
        what = esc(r["title"]) + "<small>" + esc(small) + "</small>"
        if ev and has_calendar(r):
            start = local_time(r["_date"], data["start"], tz)
            end = local_time(r["_date"], data["end"], tz)
            what += ('<span class="addcal"><a href="assets/events/%s" download>Add to calendar &darr;</a>'
                     '<a href="%s" target="_blank" rel="noopener">Google &nearr;</a></span>'
                     % (ics_name(r), html.escape(gcal_link(r, start, end))))
        c, label = chip(r)
        out += ['  <div class="%s">' % cls,
                '    <span class="date">%s</span>' % date_label(r["_date"]),
                '    <span class="what">%s</span>' % what,
                '    <span class="%s">%s</span>' % (c, label),
                '  </div>']
    out.append("</div>")
    return out


def breaks_region(rows):
    return ['<span class="chip">No meeting %s %s %s</span>' % (month_day(r["_date"]), DOT, esc(r["title"]))
            for r in rows if r["kind"] == "break"]


def next_region(rows, data, today):
    upcoming = [r for r in rows if r["kind"] != "break" and r["status"] != "done" and r["_date"] >= today]
    if upcoming:
        r = upcoming[0]
        inner = "Next block: <b>%s</b> %s %s" % (month_day(r["_date"]), DOT, esc(r.get("hero", r["title"])))
    else:
        inner = esc(data.get("wrap_line", "Fall semester is a wrap. The spring schedule drops in the GroupMe first."))
    return ['<p class="nextblock mono reveal reveal-d4" id="nextblock">%s</p>' % inner]


def jsonld_region(rows, data, tz):
    site = data["site"]
    events_url = site + "events.html"
    objs = []
    for r in rows:
        if not has_calendar(r):
            continue
        start = local_time(r["_date"], data["start"], tz)
        end = local_time(r["_date"], data["end"], tz)
        virtual = r["format"] == "virtual"
        o = {"@context": "https://schema.org", "@type": "Event",
             "name": r["title"], "description": r["description"],
             "startDate": start.isoformat(), "endDate": end.isoformat(),
             "eventStatus": "https://schema.org/EventScheduled",
             "eventAttendanceMode": "https://schema.org/%sEventAttendanceMode" % ("Online" if virtual else "Offline"),
             "location": {"@type": "VirtualLocation", "url": events_url} if virtual else PLACE,
             "isAccessibleForFree": True}
        if r.get("speaker"):
            p = {"@type": "Person", "name": r["speaker"]}
            if r.get("role"):
                p["jobTitle"] = r["role"]
            if r.get("org"):
                p["worksFor"] = {"@type": "Organization", "name": r["org"]}
            o["performer"] = p
        o["organizer"] = dict(ORGANIZER, url=site)
        o["image"] = site + "assets/og-card.jpg"
        o["url"] = events_url
        objs.append(o)
    out = ['<script type="application/ld+json">', "["]
    for i, o in enumerate(objs):
        out.append("  {")
        items = list(o.items())
        for j, (k, v) in enumerate(items):
            out.append("    %s: %s%s" % (json.dumps(k), json.dumps(v, ensure_ascii=False),
                                         "," if j < len(items) - 1 else ""))
        out.append("  }," if i < len(objs) - 1 else "  }")
    out += ["]", "</script>"]
    if any("</script" in line.lower() for line in out[1:-1]):
        fail("a schedule string contains '</script', which would break the JSON-LD block")
    return out


# ---------------------------------------------------------------- .ics
def ics_escape(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line, limit=75):
    """RFC 5545 3.1: physical lines of at most 75 octets, continued with CRLF + space."""
    out, cur, used = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if used + n > limit:
            out.append(cur)
            cur, used = " " + ch, 1 + n
        else:
            cur, used = cur + ch, used + n
    out.append(cur)
    return "\r\n".join(out)


def ics_text(r, data, tz, stamp):
    d = r["_date"]
    start = local_time(d, data["start"], tz)
    end = local_time(d, data["end"], tz)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:" + PRODID, "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "BEGIN:VEVENT",
             "UID:ch-%s@%s" % (d.strftime("%Y%m%d"), UID_DOMAIN),
             "DTSTAMP:" + stamp,
             "DTSTART:" + utc_stamp(start),
             "DTEND:" + utc_stamp(end),
             "SUMMARY:" + ics_escape("Crypto Hogs: " + r["short"]),
             "DESCRIPTION:" + ics_escape(r["calendar_description"]),
             "LOCATION:" + ics_escape(location_text(r)),
             "URL:" + data["site"] + "events.html",
             "STATUS:CONFIRMED",
             "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(fold(l) for l in lines) + "\r\n"


def write_ics(rows, data, tz):
    ICS_DIR.mkdir(parents=True, exist_ok=True)
    now_stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    keep = set()
    for r in rows:
        if not has_calendar(r):
            continue
        path = ICS_DIR / ics_name(r)
        keep.add(path.name)
        old = path.read_bytes() if path.exists() else None
        if old is not None:
            m = re.search(rb"DTSTAMP:(\d{8}T\d{6}Z)", old)
            if m and ics_text(r, data, tz, m.group(1).decode()).encode("utf-8") == old:
                report(path, False)
                continue
        path.write_bytes(ics_text(r, data, tz, now_stamp).encode("utf-8"))
        report(path, True)
    for stale in sorted(ICS_DIR.glob("*.ics")):
        if stale.name not in keep:
            stale.unlink()
            print("  removed   %s (no confirmed row with that date and slug)" % stale.relative_to(ROOT))


# ---------------------------------------------------------------- splicing
MARK = re.compile(r"^([ \t]*)<!-- schedule:([a-z]+):start -->[ \t]*\r?\n.*?^[ \t]*<!-- schedule:\2:end -->",
                  re.S | re.M)


def splice(path, regions):
    text = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in text else "\n"
    found = set()

    def sub(m):
        indent, name = m.group(1), m.group(2)
        if name not in regions:
            fail("%s has an unknown region '%s'" % (path.name, name))
        found.add(name)
        body = eol.join((indent + line) if line else "" for line in regions[name])
        return "%s<!-- schedule:%s:start -->%s%s%s%s<!-- schedule:%s:end -->" % (
            indent, name, eol, body, eol, indent, name)

    new = MARK.sub(sub, text)
    missing = set(regions) - found
    if missing:
        fail("%s is missing the marker pair(s) for: %s" % (path.name, ", ".join(sorted(missing))))
    changed = new != text
    if changed:
        path.write_bytes(new.encode("utf-8"))
    report(path, changed)
    return changed


def stamp_sitemap(loc, today):
    text = SITEMAP.read_bytes().decode("utf-8")
    pat = re.compile(r"(<url><loc>%s</loc><lastmod>)\d{4}-\d{2}-\d{2}(</lastmod>)" % re.escape(loc))
    new, n = pat.subn(lambda m: m.group(1) + today.isoformat() + m.group(2), text)
    if n != 1:
        fail("sitemap.xml has no <url> entry for " + loc)
    if new != text:
        SITEMAP.write_bytes(new.encode("utf-8"))
        print("  lastmod   %s -> %s" % (loc, today.isoformat()))


def report(path, changed):
    print("  %s %s" % ("written  " if changed else "unchanged", path.relative_to(ROOT)))


# ---------------------------------------------------------------- main
def main():
    data, rows = load()
    tz = get_tz(data["timezone"])
    today = dt.datetime.now(tz).date()
    print("build-schedule: %d rows from %s" % (len(rows), SRC.relative_to(ROOT)))
    ev_changed = splice(ROOT / "events.html", {
        "rows": rows_region(rows, data, "events.html", tz),
        "breaks": breaks_region(rows),
        "jsonld": jsonld_region(rows, data, tz),
    })
    ix_changed = splice(ROOT / "index.html", {
        "rows": rows_region(rows, data, "index.html", tz),
        "breaks": breaks_region(rows),
        "next": next_region(rows, data, today),
    })
    write_ics(rows, data, tz)
    if ev_changed:
        stamp_sitemap(data["site"] + "events.html", today)
    if ix_changed:
        stamp_sitemap(data["site"], today)
    print("done")


if __name__ == "__main__":
    main()
