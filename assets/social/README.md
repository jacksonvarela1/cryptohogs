# Social graphics

`speaker-card.html` renders one 1080x1350 Instagram post per confirmed speaker night,
in the site's own colors and type. The PNGs next to it are the exports.

## To add or change a night

1. Open `speaker-card.html` and edit the `EVENTS` block near the bottom. One entry per
   night: `day`, `title` (wrap the accent words in `<em>` for the serif italic),
   `who`, `note`, `where`.
2. Serve the repo and screenshot it. From Git Bash in the repo root:

   ```
   python -m http.server 4990 --bind 127.0.0.1 &
   "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu \
     --force-device-scale-factor=1 --hide-scrollbars --window-size=1080,1350 \
     --user-data-dir=/tmp/chshot --virtual-time-budget=15000 \
     --screenshot=assets/social/2026-10-20-my-talk-1080x1350.png \
     "http://127.0.0.1:4990/assets/social/speaker-card.html?e=2026-10-20"
   ```

3. Look at the PNG before posting it.

## Rules baked into the template, leave them in

- The talk headline is the subject, never a company name. ASG funding requires that no
  talk be framed as a company showcase.
- Every card carries "Free and open to all University of Arkansas students. No experience
  or crypto ownership required."
- Every card carries the registered student organization line. The club is not an official
  unit of the University of Arkansas.
- Only confirmed speakers get a card. Everything else is Speaker TBA.
