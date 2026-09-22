PDFS := sample_report.pdf oai-sample-report.pdf

.PHONY: all clean

all: $(PDFS)

sample_report.pdf: sample_report.typ report-template.typ octoco-report-brand.typ $(wildcard assets/octoco-report/*) $(wildcard assets/sample-report/*)
	typst compile "$<" "$@"

oai-sample-report.pdf: oai-sample-report.typ report-template.typ oai-report-brand.typ $(wildcard assets/oai-report/*) $(wildcard assets/sample-report/*)
	typst compile "$<" "$@"

clean:
	rm -f $(PDFS)
