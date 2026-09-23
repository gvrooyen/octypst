# Octypst

Octypst is a [Typst](https://typst.app/) template for technical reports. One file defines the report layout, headings, footers, figures, and other shared elements. A separate brand file supplies the logo, cover image, and colours.

Two complete examples are included:

| Report | Brand definition | Output |
| --- | --- | --- |
| `sample_report.typ` | `octoco-report-brand.typ` | `sample_report.pdf` |
| `oai-sample-report.typ` | `oai-report-brand.typ` | `oai-sample-report.pdf` |

The Octoco AI brand uses the dark imagery, `OCTOCO.AI` wordmark, and blue colours from [octoco.ai](https://octoco.ai). Its footer logo uses dark lettering so it remains legible on white pages.

Report text and layout are plain-text files. People and agents can edit them, review changes in Git, and compile a new PDF. Keep the source files under version control; the PDF can be rebuilt when needed.

## Report preview

![Sample report cover](assets/sample-report/report-cover.png)

![Sample report content](assets/sample-report/report-content.png)

## Quick start

### Prerequisites

- [Typst](https://github.com/typst/typst/releases) 0.13.1
- GNU Make

Clone the repository and build both branded samples:

```sh
git clone https://github.com/gvrooyen/octypst.git
cd octypst
make
```

Run `make clean` to remove generated PDFs. To compile one report directly:

```sh
typst compile sample_report.typ
typst compile oai-sample-report.typ
```

### Add the template to an existing Git project

Keep an Octypst checkout on your machine and expose its `bin` directory once:

```sh
git clone https://github.com/gvrooyen/octypst.git "$HOME/octypst"
export PATH="$HOME/octypst/bin:$PATH"
```

From the root of another project, create a self-contained Octoco-branded report folder:

```sh
new-report reports/design
typst watch reports/design/report.typ reports/design/report.pdf
```

The new folder contains `report.typ`, the shared template, the Octoco brand file and images, writing guidance in `AGENTS.md`, `OCTYPST-LICENSE`, and a `.gitignore` for PDFs. The command will not overwrite an existing folder.

### Live PDF preview in an Amp orb

From this repository or a folder created by `new-report`, run:

```sh
amp orb services ensure
```

Open the **Report preview** portal URL printed by Amp. The source repository previews `sample_report.typ` by default. A generated project previews `report.typ`. To preview another file, such as the Octoco AI sample, add this under `pdf-preview` in `.amp/services.yaml`:

```yaml
env:
  OCTYPST_PREVIEW_SOURCE: oai-sample-report.typ
```

Then run `amp orb service restart pdf-preview`. You can also add `--source path/to/report.typ` to the service command. Outside Amp, run `python3 scripts/pdf_preview.py --source path/to/report.typ` and open the local address it prints.

The service checks Typst files and images for changes every 0.5 seconds. When a file changes, it rebuilds the PDF and page images. The viewer keeps its scroll position. **Open PDF** opens a separate PDF whose text can be selected and downloaded.

If a build fails, the viewer shows an error and keeps the last successful version. Check `amp orb service logs pdf-preview` for details. The generated preview files live in the ignored `.amp/preview/` folder; portal records live in the ignored `.amp/portals/` folder. After a visual change, inspect the cover, a body page, and affected tables or figures. You can comment on a rendered page with the portal's review button.

## Use the structural template

Import the structural template and a brand, instantiate the template, and select the helpers the document uses:

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

The template also provides `notice`, `callout`, `report-figure`, `checkbox`, `O`, `X`, `h2`, `h3`, `fig-caption`, `cite`, and `reference`. See either sample report for examples.

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
- `heading` styles level-one and level-two headings and primary accents.
- `subheading` styles level-three headings.
- `caption` styles figure and table captions.

To change a report's brand, import another brand file and pass it to `report-template`. The report content and layout stay the same.

## Repository layout

| Path | Purpose |
| --- | --- |
| `report-template.typ` | Brand-neutral report structure and helpers. |
| `octoco-report-brand.typ` | Octoco logo, cover, and colours. |
| `oai-report-brand.typ` | Octoco AI logo, cover, and colours. |
| `starter_report.typ` | Minimal Octoco report copied by `new-report`. |
| `sample_report.typ` | Complete fictional Octoco example. |
| `oai-sample-report.typ` | Complete fictional Octoco AI example. |
| `bin/new-report` | Creates a self-contained report folder in another project. |
| `scripts/pdf_preview.py` | Builds the PDF and page images for a viewer that keeps its scroll position. |
| `.amp/services.yaml` | Supervised preview service and portal for Amp orbs. |
| `assets/*-report/` | Brand-specific assets. |
| `assets/sample-report/` | Illustrations shared by the samples. |
| `tests/table-alignment.typ` | Checks wrapped table cells aligned left, centre, and right. |

## Font configuration

The default fonts are Lato, Open Sans, and Liberation Sans for body text; Liberation Sans for headings; and Liberation Mono for code. To use other installed fonts, set these variables when running `make`:

```sh
OCTOCO_BODY_FONT="Open Sans" \
OCTOCO_HEADING_FONT="Lato" \
OCTOCO_MONO_FONT="Liberation Mono" \
make
```

When invoking Typst directly, pass the equivalent `--input body-font=...`, `--input heading-font=...`, and `--input mono-font=...` options.

## Regression check

Run the complete build and table-layout regression check with:

```sh
make check
```

The check builds both sample reports. It also compares a rendered table with a saved SVG image. That table contains wrapped text aligned left, centre, and right. The comparison catches stretched spacing in table cells and changes to column alignment. Update the saved image only after inspecting an intended layout change.

## Human and agent collaboration

1. Keep report text, structure, and style changes in `.typ` files.
2. Review source diffs, especially facts, client information, figures, and approval language.
3. Run `make check` and inspect affected rendered pages before sharing.
4. Commit source and assets; do not commit generated PDFs.

## Building in Amp orbs

The `.agents/setup` script installs Typst 0.13.1 and the required fonts in a fresh Amp orb. It then compiles the sample report to check the setup.

## License

This project is licensed under the [MIT License](LICENSE).
