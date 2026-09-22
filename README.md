# Report templates

This repository contains a reusable Typst report structure and separate brand definitions. The report layout, typography, headings, footers, figures, notices, and helper functions live in one structural template; a brand file supplies only the logo, cover artwork, and colors.

Two complete examples are included:

| Report | Brand definition | Output |
| --- | --- | --- |
| `sample_report.typ` | `octoco-report-brand.typ` | `sample_report.pdf` |
| `oai-sample-report.typ` | `oai-report-brand.typ` | `oai-sample-report.pdf` |

The Octoco AI brand uses the dark technical imagery, `OCTOCO.AI` wordmark, and blue palette from [octoco.ai](https://octoco.ai). Its footer logo is a dark-on-transparent variant so that it remains legible on white pages.

## Build the reports

Install [Typst](https://typst.app/docs/) 0.13 or newer, then run:

```sh
make
```

This builds both sample PDFs. To build one report directly:

```sh
typst compile sample_report.typ
typst compile oai-sample-report.typ
```

Run `make clean` to remove generated PDFs.

## Use the structural template

Import the structural template and the desired brand, instantiate the template, and select the helpers the document uses:

```typst
#import "report-template.typ": report-template
#import "oai-report-brand.typ": oai-brand

#let template = report-template(oai-brand)
#let (
  report,
  cover-page,
  title-page,
  report-outline,
  h1,
) = template

#show: report.with(
  document-title: "Project Report",
  document-author: "Octoco AI",
)

#cover-page(
  title: "Project Report",
  subtitle: "Project subtitle",
)

#title-page(
  title-lines: ("Project", "Report"),
  prepared: "Prepared by Octoco AI",
  version: "1.0",
  author: "Project Team",
)

#report-outline()
```

The template also exposes `notice`, `callout`, `report-figure`, `checkbox`, `O`, `X`, `h2`, `h3`, `fig-caption`, `cite`, and `reference`. See either sample report for complete usage.

## Create or swap a brand

A brand file exports a dictionary with this shape:

```typst
#let example-brand = (
  logo: "assets/example-report/logo.svg",
  front-page-image: "assets/example-report/cover-background.png",
  colors: (
    heading: rgb("#123456"),
    subheading: rgb("#345678"),
    caption: rgb("#567890"),
  ),
)
```

- `logo` appears in the footer from page 2 onward.
- `front-page-image` fills the cover page behind its title and subtitle.
- `heading` styles level-one and level-two headings and the primary accent used by rules, notices, callouts, and checked boxes.
- `subheading` styles level-three headings.
- `caption` styles figure and table captions.

To rebrand a report, import a different brand file and pass its dictionary to `report-template`. Report content and structural helpers do not need to change.

Brand assets are grouped under `assets/octoco-report/` and `assets/oai-report/`. Content illustrations shared by both samples live under `assets/sample-report/`.
