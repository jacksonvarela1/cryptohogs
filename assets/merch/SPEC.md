# Crypto Hogs shirts, print spec

Everything here is club art. No University of Arkansas mark appears in any file, so any
printer can run these today without a licensing conversation. The steps for asking about a
UARK version later are at the bottom.

Regenerate every file with:

```bash
python tools/build-merch.py
```

Colors, letterforms and the boar all live in that one script. There is no font file, no
image file and no CDN anywhere in the artwork.

## Files

| File | What it is |
| --- | --- |
| `design-a-left-chest.svg` | Left chest coin mark, bronze on a dark blank, one screen |
| `design-b-back-full.svg` | Full back print, three screens, cream and bronze and cardinal |
| `design-c-back-onecolor-cream.svg` | The same back print in one color, for dark blanks |
| `design-c-back-onecolor-ink.svg` | The same back print in one color, for light blanks |
| `proof-alphabet.svg` | Every letterform plus the boar and the coin, for checking the art |
| `mockup-*.png` | What each design looks like on a shirt, drawn to real proportions |

## Palette

| Name | Hex | Where it goes |
| --- | --- | --- |
| Ink | `#0B0B0D` | The dark blank, and the ink color on a light blank |
| Cream | `#F4EFE4` | The wordmark and the small type on a dark blank |
| Bronze | `#C9A96A` | The boar, the coin, the hairline rules |
| Cardinal | `#C41230` | The two line tagline only |
| Cardinal deep | `#9D2235` | Alternate for the tagline if the printer's red runs hot |

Ask the printer for the closest standard plastisol match and get a press proof before the
full run. Do not let a shop substitute a bright athletic red for the cardinal. That reads
as a university athletics cue, which this art is deliberately staying away from.

## Screen counts

| Design | Screens | Notes |
| --- | --- | --- |
| A, left chest | 1 | Bronze only |
| B, full back | 3 | Cream, bronze, cardinal |
| C, full back | 1 | Cheapest option, the boar loses its eye because a knockout needs a second color |

Running A and B together on the same shirt is 4 screens.

## Placement, in inches

**Design A, left chest.** Art is 3.5 in wide and 3.1 in tall. Center of the art sits 3 in
from the center front seam toward the wearer's left, with the top edge 7 in below the high
point of the shoulder.

**Designs B and C, full back.** Art is 11 in wide and 16.1 in tall. Center it on the back
with the top edge 3 in below the collar seam. It fits a standard 12 by 16 platen with room
on all four sides. Scale down to 10 in wide for youth or small adult sizes.

## The sponsor zone

The back print ends in a dashed box under a PRESENTED BY label. The box is 5.4 in wide and
1.2 in tall at the 11 in print size.

Suggested rules, for Jackson to confirm before anything is promised to a sponsor:

- One logo, one color, printed in the same ink as the type around it. No full color logos,
  no gradients, no second brand color. This keeps the screen count flat.
- The logo never gets wider than the box and never wider than half the CRYPTO HOGS
  wordmark above it.
- The dashed box is a guide, not art. Delete it when a logo goes in, or delete both the box
  and the PRESENTED BY label when the shirt ships without a sponsor.
- If no sponsor claims it, the label and the box come off. An empty box on a shirt looks
  like a mistake.
- Money question, not an art question: check with ASG before assuming ASG money can pay for
  apparel. Student government funding rules commonly exclude clothing and giveaways. Plan
  on sponsor money for shirts until someone confirms otherwise in writing.

## Blanks at three price points

All prices are estimates for a 100 piece order in 2026, before tax, and are here to size
the decision, not to quote it. Get a real quote from a Northwest Arkansas shop before
committing.

| Tier | Blank | Estimated cost each |
| --- | --- | --- |
| Value | Gildan 5000 heavy cotton | about $3.75 |
| Middle | Bella Canvas 3001 or Next Level 3600 | about $6.25 |
| Premium | Comfort Colors 1717, garment dyed | about $10.50 |

Estimated printing, per shirt at 100 pieces: one color one location about $3.25, three
colors one location about $6.25, and about $2.75 to add a one color left chest. Screen
setup runs about $22 per screen and is often waived at 100 pieces.

## Cost model, one 100 shirt run

| Run | Math | Estimated total |
| --- | --- | --- |
| Cheapest: Gildan 5000, design C only | 100 x ($3.75 + $3.25) + $22 setup | about $722 |
| Middle: Bella 3001, designs B and A | 100 x ($6.25 + $6.25 + $2.75) + $88 setup | about $1,613 |
| Premium: Comfort Colors, designs B and A | 100 x ($10.50 + $6.25 + $2.75) + $88 setup | about $2,038 |

Add roughly 9.75 percent Fayetteville sales tax if the shop charges it.

A single $2,500 Partner sponsorship covers the premium run outright with a few hundred
dollars left over, covers the middle run with about $700 left for a second small batch, or
covers the cheapest run nearly three times. That is the number to put in front of a
sponsor: one Partner check puts a shirt on every regular in the room.

## Earn a shirt on your third Tuesday

Dues are $0 and should stay $0. So do not sell these. Give a shirt to a member the third
Tuesday they show up.

- It costs nothing to a student who is already coming.
- It bounds the spend. Only regulars earn one, so 100 shirts covers a semester of regulars
  against an average of 40 in the room.
- It gives a first timer a concrete reason to come back twice more.
- The count is easy to keep next to the sign in sheet, no app required.

## Getting the strokes ready for the press

Every letter is a stroked path, not a filled outline. Any printer's RIP will handle it, but
the safe move is to expand the strokes once before output: in Illustrator open the SVG,
select all, then Object, Path, Outline Stroke, and save as a PDF. Do that on a copy. The
SVG files here stay as the editable master.

The art is vector, so it scales to any size with no quality loss. Send the SVG or the
outlined PDF, never a screenshot.

## Asking about a University of Arkansas version later

These shirts carry no university mark on purpose. Crypto Hogs is a registered student
organization, not an official unit of the University of Arkansas, and putting a UA mark
next to a sponsor logo would read as the university endorsing a company. If the club ever
wants an officially marked version, this is the path:

1. Find the current contact. Search `uark.edu` for "Trademark Licensing" and use the email
   listed on that office's page. Do not rely on a number or address from anywhere else.
2. Send one email that asks four things: the approval process for registered student
   organization merchandise, whether the club has to order through a licensed vendor,
   whether internal RSO orders are exempt from royalties, and the turnaround time for art
   approval.
3. Expect to submit the art as a PDF and to wait for written approval before printing. Keep
   that approval email with the club records.
4. Ask explicitly about putting a sponsor logo on the same garment as a university mark.
   Assume the answer is no until it is yes in writing.
5. Keep the non-endorsement line in club materials either way.

Until that comes back approved, print the files in this folder. They are club art, they are
free of any university mark, and they are ready to go.
