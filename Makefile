SOURCE := sample_report.typ
PDF := sample_report.pdf

.PHONY: all clean

all: $(PDF)

$(PDF): $(SOURCE) octoco-report-template.typ $(wildcard assets/octoco-report/*)
	typst compile "$<" "$@"

clean:
	rm -f $(PDF)
