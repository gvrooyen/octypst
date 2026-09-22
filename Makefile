PDFS := sample_report.pdf oai-sample-report.pdf
TYPST_INPUTS :=

ifneq ($(strip $(OCTOCO_BODY_FONT)),)
TYPST_INPUTS += --input body-font="$(OCTOCO_BODY_FONT)"
endif

ifneq ($(strip $(OCTOCO_HEADING_FONT)),)
TYPST_INPUTS += --input heading-font="$(OCTOCO_HEADING_FONT)"
endif

ifneq ($(strip $(OCTOCO_MONO_FONT)),)
TYPST_INPUTS += --input mono-font="$(OCTOCO_MONO_FONT)"
endif

.PHONY: all check clean FORCE

all: $(PDFS)

# The phony prerequisite ensures a changed font environment rebuilds the PDFs.
sample_report.pdf: FORCE sample_report.typ report-template.typ octoco-report-brand.typ $(wildcard assets/octoco-report/*) $(wildcard assets/sample-report/*)
	typst compile $(TYPST_INPUTS) "sample_report.typ" "$@"

oai-sample-report.pdf: FORCE oai-sample-report.typ report-template.typ oai-report-brand.typ $(wildcard assets/oai-report/*) $(wildcard assets/sample-report/*)
	typst compile $(TYPST_INPUTS) "oai-sample-report.typ" "$@"

check: all
	@tmp="$$(mktemp)"; \
	trap 'rm -f "$$tmp"' EXIT; \
	typst compile --root . --format svg tests/table-alignment.typ "$$tmp"; \
	cmp --silent tests/table-alignment-reference.svg "$$tmp" || { \
		echo "Table alignment regression differs from tests/table-alignment-reference.svg" >&2; \
		exit 1; \
	}

FORCE:

clean:
	rm -f $(PDFS)
