#import "report-template.typ": report-template
#import "octoco-report-brand.typ": octoco-brand

#let (
  report,
  cover-page,
  title-page,
  report-outline,
) = report-template(octoco-brand)

#set page(numbering: "1")

#show: report.with(
  document-title: "Project Report",
  document-author: "Your organisation",
)

#cover-page(
  title: "Project Report",
  subtitle: "A concise project summary",
)

#title-page(
  title-lines: ("Project Report",),
  prepared: "Prepared for [CLIENT]",
  version: "0.1",
  author: "Author",
)

#report-outline(depth: 2)
#pagebreak()

= Executive Summary

State the purpose, current status, and decisions needed from this report.

= Scope

Describe the work covered by this report and the important boundaries.

== Objectives

- Record the intended outcomes.
- Identify assumptions and constraints.
