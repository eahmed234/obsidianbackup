# nabiwiki visual design — specification

The look the user approved on 13 Nov 2026. The four HTML files beside this one are the reference: open them
in a browser (`article-light.html`, `article-dark.html`, `phone-light.html`, `phone-dark.html`). They are
hand-written mockups with inline styles — **copy the look, not the markup**. The site is still built by
Quartz plus the `site_*.py` post-build steps (see `docs/site.md`); the work is to make those produce this.

Nothing here changes a note. Do not edit any `*.md` in the vault root.

## Tokens

| Role | Light | Dark | Quartz colour key |
| --- | --- | --- | --- |
| Page ground | `#ffffff` | `#15171a` | `light` |
| Rules, borders | `#e3e5e8` | `#2c3036` | `lightgray` |
| Secondary text, labels | `#555b63` | `#a3a9b2` | `gray` |
| Body text | `#1b1d1f` | `#e6e8eb` | `darkgray` |
| Headings | `#1b1d1f` | `#e6e8eb` | `dark` |
| Links, active item | `#1d5c4d` | `#7cc7b0` | `secondary` |
| Link hover | `#0d3229` | `#a6e0cd` | `tertiary` |
| Panel ground (sidebar, infobox, blockquote) | `#f6f7f8` | `#1d2024` | add `--panel` in `custom.scss` |
| Highlight | `rgba(29, 92, 77, 0.10)` | `rgba(124, 199, 176, 0.14)` | `highlight`, `textHighlight` |
| Notice ground / border / text | `#fff8e6` / `#ecd9a6` / `#6b4a00` | `#2a2413` / `#5c4a1a` / `#e9c979` | add `--notice-*` in `custom.scss` |

Every text/ground pair above is at least 6.4:1. Keep it so: nothing below 4.5:1 in either mode, including
grey labels, chips, the notice, search results, popovers, code and tables. The purple accent goes entirely.

Dark mode is a first-class target, not an afterthought: every rule that sets a colour must use a variable
that changes with the mode (Quartz sets `:root[saved-theme="dark"]`). No hard-coded hex outside the two
variable blocks. Check in dark: infobox, chips, notice, sidebar active item, blockquotes, footnote
popovers, search box and results, tables (asbāb al-nuzūl), disambiguation pages, tag pages, the 404 page.

## Type

- Body and headings: **Source Serif 4** (400, 600, italic 400). It carries the IJMES diacritics. Fallback
  Georgia, serif.
- Interface (sidebar, infobox, breadcrumbs, notes, buttons, search): **Inter** (400, 500, 600).
- Arabic: **Noto Naskh Arabic** (400, 600), as now. The honorific ligatures (ﷺ ﵁ ﵂ ﵃ ﵄ ﵅ ﵊) must still
  render after the font change — check a page that uses them (`Abū Dujānah`) before and after.
- Body 18px / 1.65 on desktop, 17px on phones. `h1` 40px (32px phone), weight 600, with the Arabic name
  beside it in Naskh at 30px (24px phone), muted. `h2` 26px (22px phone), weight 600, with a 1px rule under
  it. Epithet line: italic, muted, body size.
- Arabic quotations: Naskh 24px / 1.9, right-to-left, in a panel-ground block with 8px radius and no left
  border; the English beneath in muted body text.

## Layout

- Desktop: three columns inside a 1360px container with 32px padding and 40px gaps — contents sidebar
  (≈240px, panel ground, 8px radius), article (max 780px), "On this page" (≈200px). Header: site name with
  «السيرة», search box (max 420px, 44px tall), one text link.
- Phone (≤ 800px): one column, 16px side padding. Header is a menu button, the site name, then the search
  box on its own row. Infobox goes full width **after the lead paragraph**. Sidebar opens from the menu
  button. Nothing scrolls sideways except wide tables, inside their own box.
- Above the article, in this order: breadcrumb (hub › section), title + Arabic, epithet, the notice.
  **Remove** from above the article: the tag list, the date, the reading time, reader-mode button.
- Infobox: floated right, 300px, panel ground, 1px border, 8px radius; title, Arabic, chips (role tags),
  then label/value rows separated by 1px rules. It already comes from `site_nav.py`; restyle it.
- Contents sidebar: section headings; **only the section holding the current page is open**, showing a
  few neighbours either side and a "Show all N…" link; the current page is marked with a bordered pill.
- Notice ("Unverified entry"): one slim bordered box with an icon, at most two lines:
  "**Not yet checked by a person.** This entry was written from the cited pages and is awaiting review
  against the books." It comes from `site_notice.py`.
- Footnotes: small sans superscript numbers in the text; the list at the foot in 13.5px Inter, muted.
- Foot of the article: before/after links as two bordered cards (already produced by `site_nav.py`), then
  backlinks.
- Touch targets ≥ 44px. Links are distinguishable without colour alone (underline on hover is enough for
  body links; nav links may be plain).

## Where each change goes

| Change | File |
| --- | --- |
| Colours (both modes), fonts | `quartz.config.yaml` (`theme.colors`, `theme.typography`) |
| Everything else visual | `custom.scss` |
| Turn off tag list, date/reading time, reader mode above the article | `quartz.config.yaml` plugin `enabled:` flags |
| Sidebar: open only the current section, neighbours, "Show all" | `site_nav.py` |
| Notice wording and markup | `site_notice.py` |

Do not edit `patch-quartz.mjs` or raise `QUARTZ_REF` for this. If a Quartz class name is needed, read it
from the built HTML in `public/`, not from memory.

## Done when

1. `bash build.sh` passes (it runs the audit and the search checks).
2. In the built `public/`, these pages look like the reference in **light and dark**, at 1360px and 390px
   wide: `ghazwat-al-suwayq`, `abu-dujanah` (person, honorifics), a sūrah page with a table, `the-sirah`
   (hub), `start-here` (homepage), a tag page, and a search for "Abu Bakr".
3. No purple remains; no hard-coded colour outside the variable blocks; no contrast pair under 4.5:1.
4. `docs/site.md` describes the new sidebar behaviour and plugin changes; `CLAUDE.md`/`GEMINI.md` stay
   identical apart from their first two lines if either is touched.
5. Committed on `drafts`. The user has said this change may then be published: `git push origin drafts:main`
   (an exception to the standing "agents never push" rule, for this change only). The push asks the user
   for approval in the session; after it, check that the Pages deploy succeeded (`gh run list --limit 1`).
