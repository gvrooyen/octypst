SOURCE := sample_report.typ
PDF := sample_report.pdf
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

.PHONY: all clean FORCE

all: $(PDF)

# The phony prerequisite ensures a changed font environment rebuilds the PDF.
$(PDF): FORCE $(SOURCE) octoco-report-template.typ $(wildcard assets/octoco-report/*)
	typst compile $(TYPST_INPUTS) "$(SOURCE)" "$@"

FORCE:

clean:
	rm -f $(PDF)
