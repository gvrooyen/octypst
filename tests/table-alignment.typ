#import "../report-template.typ": report-template
#import "../octoco-report-brand.typ": octoco-brand

#let (report,) = report-template(octoco-brand)

#show: report.with(
  document-title: "Table alignment regression",
  document-author: "Octypst",
)

#set page(width: 150mm, height: 72mm, margin: 12mm, footer: none)

#text(size: 12pt, weight: "bold")[Table paragraph alignment]

#v(8pt)

#table(
  columns: (1fr, 1fr, 1fr),
  align: (left, center, right),
  inset: 6pt,
  stroke: 0.5pt + luma(160),
  table.header(
    [*Left aligned*],
    [*Centered*],
    [*Right aligned*],
  ),
  [Alpha beta gamma delta epsilon zeta],
  [Alpha beta gamma delta epsilon zeta],
  [Alpha beta gamma delta epsilon zeta],
)
