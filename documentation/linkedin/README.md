# LinkedIn, kept in step with dennis.gesker.com

## Why this is a document and not a script

LinkedIn has no API for editing a personal profile. Its public APIs cover
sharing and marketing surfaces; the profile itself is web-only, behind the
account's own login, and driving that with automation breaks the User Agreement
and puts the account at risk. The account is a career asset — it does not get
automated behind your back. So this is the copy, the sizes, and the order to
paste it in. Twenty minutes, once.

## What "matching the website" means here

| Field | Website source | Rule |
| --- | --- | --- |
| Name | `src/hero.md` | `Dennis R. Gesker` |
| Headline | hero eyebrow + résumé role line | names the three target titles, then the stack |
| About | Executive Profile + Selected Highlights + Leadership Value | numbers first, adjectives last |
| Experience | `src/professional/*.md` | titles and dates identical to the résumé |
| Skills | `src/foundational_technologies_content.md` | 50 slots, ordered so the top row is leadership, not tools |
| Banner | `documentation/linkedin/linkedin-banner.jpg` | 1584×396, text clear of the photo overlay |
| Photo | `documentation/linkedin/linkedin-photo.jpg` | 344×344, same crop as the website avatar |
| Website | profile contact info | `https://dennis.gesker.com` |
| Custom URL | already set | `linkedin.com/in/gesker` — matches the footer and JSON-LD `sameAs` |

Copy lives in `profile-copy.md`. Character counts are in that file and every
block fits.

## Changing the photo

The photo is in five places and one of them drifting is invisible until a
recruiter sees it. Drop the original beside this file as `profile-source.jpg`
(or any path) and run:

```
just profile-photo documentation/linkedin/profile-source.jpg
nix build && just publish
```

`scripts/profile_photo.py` regenerates the site avatar, the master portrait, the
Open Graph card, the LinkedIn photo and the LinkedIn banner at their correct
sizes, and refuses a source under 400px on the short side unless `--allow-small`
is passed. LinkedIn's own "save photo" gives a 200×200 thumbnail — the current
`profile-source.jpg` is exactly that, so the 344px avatar is upscaled 1.72×. The
camera original fixes it; nothing else needs to change.

The master portrait is never replaced by a smaller source, so the sharper
`src/images/profile_picture.jpg` survives.

## Order to do it in

1. **Banner and photo first.** They render before any text and they are what a
   recruiter sees in a search result.
2. **Headline.** This is the searchable line. It must carry the three titles you
   are actually applying for: CTO, VP Engineering, Director of Engineering. Not
   "Technology Leader".
3. **About.** Paste the whole block. LinkedIn keeps line breaks; the section
   headings are in caps so they read as headings.
4. **Experience.** Title and dates exactly as the résumé — an ATS or a recruiter
   comparing the two files must not find a contradiction. Company spelling
   matters: `Alamon, Inc.`, `Candela Global, LLC`, `Montana State University`,
   `U.S. Department of State`.
5. **Skills.** Pick the 50 from the list; the order given puts leadership and
   strategy above tooling, because LinkedIn shows the first few.
6. **Contact info.** Website `https://dennis.gesker.com`, email, phone
   `+1 202-798-3202`.
7. **Featured / media.** Link the two PDFs:
   `https://dennis.gesker.com/Dennis_Gesker_Resume_Short.pdf` (two pages) and
   `https://dennis.gesker.com/Dennis_Gesker_Resume.pdf` (full).

## Keeping them in step

The website is the source of truth: `src/` builds the résumé, the PDFs and the
JSON-LD. When those change, this file is the diff list for LinkedIn. Do not edit
LinkedIn first and then the site — the site generates the artifacts you actually
submit.

## Open question

If you want a Company page or a "Featured" article set, that is a different
surface with its own API — say so and it gets its own section here.
