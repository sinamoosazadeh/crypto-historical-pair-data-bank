# UI and UX design notes

The catalogue is a static-first single-page control center designed for GitHub Pages, local hosting, desktop browsers, and mobile screens. It has no mandatory frontend package install and requires no runtime API key.

## Main views

- **Overview:** inventory counters, Level 1/2/3 taxonomy, interval-token vocabulary, and direct paths to common tasks.
- **Coverage explorer:** keyword search, asset / interval / source / status / market filters, bounded pagination, filtered CSV export, and a link to download the full evidence matrix.
- **Source registry:** searchable source routes, strict-download eligibility state, market scope, data families, source notes, and provider links.
- **Asset universe:** the 14 initial assets with clear warnings that an asset being in scope does not establish a live listing on every venue.
- **Evidence and quality:** verification ladder and reproducible archive-inspection workflow.

## Interaction standards

- Search and filters remain usable at narrow viewport widths.
- Coverage pagination limits rendered rows instead of placing the entire matrix in the DOM.
- CSV exports use correct CSV quoting and a UTF-8 byte-order mark for spreadsheet compatibility; repository source files themselves are kept free of BOM bytes.
- Dark and light themes are supported. Theme persistence is a convenience, not a data dependency.
- Native buttons, labels, semantic tables, clear empty states, and `aria-live` toast messages support keyboard and assistive-technology usage.
- The page may register a basic service worker on HTTP(S); offline caching is optional and does not change the evidence status.

## Known limitations

- The UI is a catalogue browser, not a distributed query engine or a raw-data viewer.
- The matrix is a research snapshot; it is not revalidated automatically each time the page opens.
- Decorative sparklines are visual motifs, not measured time series. They must not be interpreted as coverage trends.
- External web fonts can fail offline; system font fallbacks are specified.
- Source links and upstream access conditions can change.
