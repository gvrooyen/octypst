#import "octoco-report-template.typ": *

#set page(numbering: "1")

#show: octoco-report.with(
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
