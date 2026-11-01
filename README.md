# StellaScrapes

> **Project status: MVP achieved · Active development**
>
> StellaScrapes has reached a working MVP milestone and remains in active development. The original application supports public-record data discovery, retrieval, processing, and structured exports. This public repository is a curated and redacted portfolio publication, not a complete copy of the production application.
>
> Core production components have been deliberately withheld, including proprietary query interpretation, dataset selection, record retrieval, normalization, filtering, and prioritization logic. Their removal means the published source cannot reproduce the complete search workflow. This is an intentional intellectual-property boundary, not an indication that the underlying application is fundamentally broken.
>
> This repository is published for portfolio inspection and technical demonstration, not as a distributable product. It is not intended to be cloned, run, repurposed, or used as a production data service. No permission is granted to copy, modify, distribute, or commercially use the published material.

**AI-assisted, human-directed development.** StellaScrapes is a public-record data discovery and processing platform built with Python and Node.js. It was designed to identify relevant open-data sources, interpret search requests, retrieve applicable records, normalize inconsistent datasets, and produce structured exports.

> **Portfolio publication — intentionally incomplete.** This repository provides a selective view of the project's architecture, supporting utilities, interface, and representative outputs. Proprietary search routing, dataset selection, record-processing, and prioritization implementations have been withheld. The omissions are deliberate: this publication is intended for technical review, not as a working copy of the production application.

## Project overview

StellaScrapes was developed to make fragmented municipal and county open-data sources more accessible through a unified search and processing workflow.

The platform uses public Socrata catalog infrastructure to discover publishing domains and datasets. Its original production workflow connects that discovery layer to a configured dataset registry, interprets natural-language search requests, retrieves applicable records, and converts inconsistent source data into a consistent output structure.

The project was designed around two primary interfaces:

- **Python command-line interface** — an interactive environment for search, source discovery, cataloguing, registry operations, and record processing.
- **Node.js web interface** — a browser-based application providing search interaction, application metadata, and CSV/XLSX export endpoints.

The original application supports structured exports in CSV and Excel formats. Its output model is intended to make records from different source datasets easier to review and work with through consistent fields.

## Data discovery and processing

The original platform separates source discovery from dataset selection and record retrieval.

Its workflow includes several distinct stages:

1. **Publishing-domain discovery** — query the public Socrata catalog and identify domains publishing datasets.
2. **Dataset cataloguing** — retrieve dataset metadata across discovered domains, including descriptions, available fields, update information, and source references.
3. **Dataset classification** — identify relevant dataset types and determine which fields can serve the platform's standardized record model. The production implementation is withheld.
4. **Search interpretation** — interpret a user's request and resolve relevant record categories, locations, and applicable filters. The production implementation is withheld.
5. **Record retrieval** — query the selected public data source and retrieve applicable records. The production implementation is withheld.
6. **Normalization and filtering** — map source-specific fields into a consistent output structure and apply relevant filtering. The production implementation is withheld.
7. **Export** — produce structured CSV and Excel files for downstream review and use.

The discovery and metadata-cataloguing components are represented in the public source. The production logic connecting catalogued datasets to live search and retrieval is not.

## Application workflow

The original application supports a command-line workflow and a browser-based interface.

**Command-line workflow**

The Python application provides an interactive menu for the platform's primary operations:

- Search configured public datasets.
- Review locations and available dataset categories.
- Discover publishing domains through the Socrata global catalog.
- Catalog datasets from individual or multiple domains.
- Run the available test suite.
- Export and process retrieved records.

The public version retains portions of the discovery, metadata retrieval, and processing structure. Its production search router and associated retrieval workflow have been withheld, so live searches cannot be completed from this publication.

**Browser workflow**

The Node.js application provides the server-side structure for the browser interface.

The original application is organized around:

- Search requests submitted through the web interface.
- Application metadata used to describe configured locations and dataset categories.
- Structured search results returned to the browser.
- CSV and XLSX export handling.
- A consistent output schema shared with the Python workflow.

The public server and interface preserve selected application structure, but the production routing and retrieval implementation is absent. The published browser application therefore cannot complete live searches.

## Architecture

StellaScrapes uses separate modules for discovery, cataloguing, routing, record processing, and presentation. Python handles the data-oriented workflow, while Node.js provides the browser-facing application and export layer.

| **Component** | **Responsibility** |
| --- | --- |
| `main.py` | Python command-line entry point and interactive application menu |
| `discover.py` | Socrata global-catalog discovery and publishing-domain collection |
| `catalog.py` | Dataset metadata retrieval and catalog generation |
| `import_catalog.py` | Catalog import and supporting registry workflow |
| `prospect_scraper.py` | Supporting public-data retrieval and prospecting workflow; production components are withheld |
| `router.py` | Python search-routing interface and structured result representation |
| `clean_permits.py` | Record cleaning, normalization utilities, and CSV/XLSX export |
| `server.js` | Express application server and browser-facing API routes |
| `lib/router.js` | Node.js routing interface and shared output schema |
| `lib/registry.js` | Registry loading and application configuration access |
| `lib/exporter.js` | CSV and Excel workbook generation |
| `public/` | Browser interface and client-side application presentation |
| `registry.json` | Sanitized public registry structure |
| `output/` | Representative, sanitized project outputs |

### Engineering considerations

Several design decisions are central to the project:

- **Discovery separated from retrieval:** identifying publishing domains and cataloguing datasets are distinct from selecting and querying records.
- **Metadata-driven architecture:** catalogued datasets provide the information needed by the production workflow to identify and configure potential sources.
- **Shared record structure:** the Python and Node.js interfaces use a consistent output model, reducing the need for separate downstream data representations.
- **Modular processing:** discovery, cataloguing, routing, normalization, and export are separated by responsibility rather than combined into one large application module.
- **Multiple interfaces:** the command-line and browser workflows are designed to use the same underlying application concepts and record structure.
- **Structured exports:** CSV and Excel generation are handled through dedicated export utilities rather than being embedded in search logic.
- **Defensive data handling:** spreadsheet-oriented exports escape formula-like text so that values are treated as data rather than executable spreadsheet formulas.
- **Source-aware operation:** public availability is not treated as blanket permission to collect, retain, combine, or republish every field.

## Technology

- Python
- Node.js
- JavaScript
- Express
- Socrata Open Data API and catalog
- JSON
- CSV
- ExcelJS
- Excel/XLSX
- SQLite and local file-based data structures where applicable

## AI-assisted development methodology

StellaScrapes was developed through an iterative, AI-assisted process. AI is disclosed as part of the development methodology, not hidden or presented as unaided authorship.

Models were used to accelerate implementation, explore alternatives, and investigate unfamiliar problems. Their output was not treated as authoritative. The engineering value comes from how the tools are directed, challenged, and held accountable to the wider application context.

### 1. Challenge the reasoning

Proposed implementations are interrogated rather than accepted at face value. Their assumptions are questioned, and design decisions are expected to have a defensible rationale. Models are allowed to explore beyond the immediate task when a detour may expose a useful conflict, application, or overlooked use case, provided the reasoning holds up. Agreement is not the objective; finding the strongest defensible solution is.

### 2. Account for failure modes

Context-window limits, conversational drift, hallucinations, and stateless API calls all affect reliability. Weak information sources and search systems that reward visibility rather than accuracy introduce further risks. A confident answer can still be wrong, incomplete, or detached from the actual implementation. Those limitations must be accounted for rather than mistaking fluency for evidence.

### 3. Verify, don't defer

Models can reframe a question, narrowly rebut a claim while missing its substance, distort emphasis, construct strawmen, or dismiss inconvenient evidence. Discussions are brought back to their original context, and disagreements are investigated rather than resolved by automatically accepting either the model's conclusion or the developer's own. Model reasoning is adopted only when it withstands scrutiny.

**The principle:** AI can generate possibilities, challenge assumptions, and accelerate execution. It cannot be trusted to police its own reasoning. That responsibility stays with the operator, who must preserve context, demand intellectual honesty, and verify that an answer has merit before building on it.

AI assistance is therefore treated as a development tool, not a substitute for engineering judgment. Responsibility for requirements, architecture, integration, review, verification, and final implementation decisions remains with the developer.

## Publication scope

This repository is deliberately incomplete as an executable application.

The public release retains selected discovery, cataloguing, metadata, interface, processing, and export components. Production implementations have been removed or replaced with non-operational interfaces, including:

- Natural-language query interpretation and routing.
- Production dataset selection and prioritization.
- Live record retrieval and source-specific query construction.
- Dataset classification and automatic field-role detection.
- Record normalization and production filtering logic.
- Selected internal registry-generation and orchestration components.

The visible source may demonstrate individual implementation patterns, but it does not contain the complete production workflow. In particular, the published router interfaces do not perform live searches, and the retained web server cannot retrieve production records without the withheld components.

Representative output files are included to demonstrate the shape and presentation of application-generated results. They have been sanitized to remove identifying record information and are not intended to provide a reusable dataset or a reconstruction of the production registry.

The repository is presented so that reviewers can examine the project's modular organization, source-discovery approach, metadata handling, interface structure, output schemas, export utilities, and engineering decisions without receiving the proprietary parts of the application.

## Data handling and limitations

StellaScrapes works with public-record and open-data sources. Public availability does not mean every field is appropriate to collect, retain, combine, or republish.

Source documentation and applicable terms should be reviewed before automating requests. Published rate limits should be respected, and access controls should not be bypassed.

The record-cleaning utilities normalize and export data; they do not anonymize or de-identify it. Exported records may contain personal or otherwise sensitive information depending on the source. Data should be reviewed before it is shared or republished.

Spreadsheet exports escape formula-like text, but this is not a substitute for reviewing the contents of an export.

The original platform depends on the availability, consistency, and quality of external publishing systems. Dataset schemas, field names, update schedules, API behavior, and source availability can change. A successful catalog discovery does not guarantee that a dataset is suitable for a particular search or that its records are complete, current, or accurate.

The public repository does not include the complete production retrieval and prioritization workflow. Its retained components should not be interpreted as a claim that every documented capability is available in this release.

## Copyright and usage

Copyright © 2026 codedByStella. All rights reserved.

This repository is published for portfolio and technical-demonstration purposes only. No permission is granted to copy, modify, distribute, sublicense, or commercially use this code without prior written authorization.
