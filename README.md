# Octypst

Octypst is a reusable [Typst](https://typst.app/) template for professional
technical project reports. It includes an Octoco-styled report layout, a
complete fictional sample report, and the graphics used by that sample.

Typst documents are well suited to human and agent collaboration. Report
content and layout are plain-text source files, so people can
review focused Git diffs while coding agents can draft sections, update tables,
or make consistent template changes. Both work against the same source of
truth; the PDF is a reproducible build artifact rather than a file that must be
manually merged.

## Report preview

![Sample report cover](assets/sample-report/report-cover.png)

*Cover page from the included sample report.*

![Sample report content](assets/sample-report/report-content.png)

*A representative content page with report headings and an architecture figure.*

## Quick start

### Prerequisites

- [Typst](https://github.com/typst/typst/releases) 0.13.1
- GNU Make

Clone the repository and build the included sample:

```sh
git clone https://github.com/gvrooyen/octypst.git
cd octypst
make
```

This writes `sample_report.pdf` to the repository root. Rebuild after editing
the report or template with `make`; the Makefile intentionally recompiles on
every invocation so a changed font configuration is picked up immediately.

To remove the generated PDF:

```sh
make clean
```

You can also invoke Typst directly:

```sh
typst compile sample_report.typ sample_report.pdf
```

### Add the template to an existing Git project

You do not need to clone this repository or add it as a Git remote. From your
existing project's root, download a source archive and copy the template and
the assets it needs. Review the files first if your project already has paths
with the same names.

```sh
tmp_dir="$(mktemp -d)"
mkdir "$tmp_dir/octypst"
curl --fail --location \
  https://github.com/gvrooyen/octypst/archive/refs/heads/main.tar.gz \
  --output "$tmp_dir/octypst.tar.gz"
tar --extract --gzip --file "$tmp_dir/octypst.tar.gz" \
  --strip-components=1 --directory "$tmp_dir/octypst"

cp "$tmp_dir/octypst/octoco-report-template.typ" .
mkdir -p assets
cp -R "$tmp_dir/octypst/assets/octoco-report" assets/
cp "$tmp_dir/octypst/LICENSE" OCTYPST-LICENSE

# Optional: include the sample report and its illustrations.
# cp "$tmp_dir/octypst/sample_report.typ" .
# cp -R "$tmp_dir/octypst/assets/sample-report" assets/
rm -rf "$tmp_dir"
```

The template expects the logo and cover artwork at `assets/octoco-report/`.
The copied `OCTYPST-LICENSE` preserves the required MIT notice. Include the
optional files if you want the full example; otherwise, create a report source
file that imports the template.

## Customize a report

1. Copy `sample_report.typ` to a new `.typ` file.
2. Update the metadata, cover page, headings, body content, tables, and figures.
3. Keep `octoco-report-template.typ` and the required `assets/` paths available.
4. Compile your document with Typst or adapt `SOURCE` and `PDF` in the Makefile.

The sample is deliberately fictional and contains redacted placeholders. It is
a template and example, not a production report or a source of real project
information.

### Typst markup at a glance

The report is ordinary, readable text with light markup for structure and
template helpers:

```typst
#import "octoco-report-template.typ": *

#show: octoco-report.with(document-title: "Project report")

#cover-page(
  title: "Technical Project Report",
  subtitle: "A concise project summary",
)

= Purpose and scope

This paragraph is the report body. Use _emphasis_ and *strong text* directly
in the source.

== Objectives

- Describe an outcome.
- Link to a figure with @architecture.

#figure([An architecture diagram goes here.]) <architecture>
```

### Repository layout

| Path | Purpose |
| --- | --- |
| `octoco-report-template.typ` | Reusable layout, typography, cover, headings, notices, figures, and report helpers. |
| `sample_report.typ` | Complete example document and starting point for new reports. |
| `assets/octoco-report/` | Octoco logo and cover-background artwork. |
| `assets/sample-report/` | Architecture and data-flow graphics used by the sample. |
| `Makefile` | Reproducible local build with optional font overrides. |

## Font configuration

The default, open-font configuration is:

- Body text: Lato, Open Sans, then Liberation Sans
- Headings: Liberation Sans
- Code: Liberation Mono

For local brand or document compatibility, override any of these using
namespaced environment variables. The selected fonts must already be installed
on your machine.

```sh
OCTOCO_BODY_FONT="Open Sans" \
OCTOCO_HEADING_FONT="Lato" \
OCTOCO_MONO_FONT="Liberation Mono" \
make
```

Each variable is optional. Unset variables retain the open-font defaults, so
the following changes only the heading family:

```sh
OCTOCO_HEADING_FONT="Your Installed Heading Font" make
```

The Makefile passes the values to Typst as document inputs. This leaves the
template’s portable defaults intact and avoids editing the template for each
local environment. Install the default font families (or your selected
overrides) locally to reproduce the intended typography.

These environment variables work through this repository's Makefile. If you
copied only the template and assets into another project, pass the corresponding
inputs to Typst directly:

```sh
typst compile \
  --input body-font="Open Sans" \
  --input heading-font="Lato" \
  --input mono-font="Liberation Mono" \
  report.typ report.pdf
```

## Human and agent collaboration

Typst and Git provide a practical workflow for mixed human/agent authorship:

1. Keep report text, structure, and style changes in `.typ` files.
2. Assign an agent a bounded change such as drafting a section, updating a
   diagram reference, or applying a styling rule.
3. Review the resulting Git diff as you would code, paying particular attention
   to facts, client information, figures, and approval language.
4. Run `make` to render the PDF and inspect the affected pages before sharing.
5. Commit the reviewed source and assets; do not commit generated PDFs.

## Building in Amp orbs

The repository includes `.agents/setup` for Amp orbs. A fresh orb installs the
pinned Typst toolchain and the open font packages, then verifies it can compile
the sample report. This makes the same defaults available to human and agent
workflows in a clean remote environment.

## License

This project is licensed under the [MIT License](LICENSE).
