
'use strict';

/*
 * StellaScrapes — Web Application Server
 *
 * Public-release server entry point.
 *
 * Provides browser access to search, record retrieval, and structured
 * data exports.
 *
 * The application is an MVP and remains in active development.
 */

const path = require('path');
const express = require('express');

const {
  route,
  OUTPUT_COLUMNS_BY_TYPE,
  DEFAULT_OUTPUT_COLUMNS
} = require('./lib/router');

const { getRegistry } = require('./lib/registry');

const { toCsv, toXlsxBuffer } = require('./lib/exporter');

const app = express();

const PORT = process.env.PORT || 3100;
const HOST = process.env.HOST || '127.0.0.1';
const MAX_QUERY_LENGTH = 500;

app.use(express.json({ limit: '32kb' }));
app.use(express.static(path.join(__dirname, 'public')));


// ── EXPORT HELPERS ──────────────────────────────────────────────────────────

function columnsFor(dataType) {
  return OUTPUT_COLUMNS_BY_TYPE[dataType] || DEFAULT_OUTPUT_COLUMNS;
}

function exportFilenameBase(result) {
  const citySlug = (result.city || 'unknown')
    .toLowerCase()
    .replace(/,/g, '')
    .replace(/\s+/g, '_');

  const typeSlug = result.data_type;
  const tradeSlug = result.trade ? `_${result.trade}` : '';

  const dateSlug = new Date()
    .toISOString()
    .slice(0, 10)
    .replace(/-/g, '');

  return `${citySlug}_${typeSlug}${tradeSlug}_${dateSlug}`;
}


// ── SEARCH ──────────────────────────────────────────────────────────────────

// GET /api/search?q=<query>

app.get('/api/search', async (req, res) => {
  const q = String(req.query.q || '').trim();

  if (!q) {
    return res.status(400).json({ error: 'A search query is required.' });
  }
  if (q.length > MAX_QUERY_LENGTH) {
    return res.status(400).json({ error: `Search query must be ${MAX_QUERY_LENGTH} characters or fewer.` });
  }

  try {
    const result = await route(q, {
      log: msg => console.log(`  ${msg}`)
    });

    const columns = columnsFor(result.data_type);

    const records = result.records.map(({ _raw, ...rest }) => rest);

    res.json({
      ...result,
      records,
      columns
    });

  } catch (e) {
    console.error('[search] unexpected error:', e);

    res.status(500).json({
      error: 'The request could not be completed. Please try again.'
    });
  }
});


// ── EXPORT ──────────────────────────────────────────────────────────────────

// GET /api/export?q=<query>&format=csv|xlsx

app.get('/api/export', async (req, res) => {
  const q = String(req.query.q || '').trim();
  const format = String(req.query.format || 'csv').toLowerCase();

  if (!q) {
    return res.status(400).json({
      error: 'q (query) is required'
    });
  }

  if (!['csv', 'xlsx'].includes(format)) {
    return res.status(400).json({
      error: "format must be 'csv' or 'xlsx'"
    });
  }

  try {
    const result = await route(q, {
      log: msg => console.log(`  ${msg}`)
    });

    if (result.error) {
      return res.status(422).json({
        error: result.error
      });
    }

    if (!result.records.length) {
      return res.status(404).json({
        error: 'No records to export for this query.'
      });
    }

    const columns = columnsFor(result.data_type);
    const base = exportFilenameBase(result);

    if (format === 'csv') {
      res.setHeader(
        'Content-Type',
        'text/csv; charset=utf-8'
      );

      res.setHeader(
        'Content-Disposition',
        `attachment; filename="${base}.csv"`
      );

      res.send(toCsv(result.records, columns));

    } else {
      const buf = await toXlsxBuffer(
        result.records,
        columns,
        {
          sheetName: result.data_type.slice(0, 31),
          title: `${result.city} — ${result.data_type}${result.trade ? ' / ' + result.trade : ''}`
        }
      );

      res.setHeader(
        'Content-Type',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );

      res.setHeader(
        'Content-Disposition',
        `attachment; filename="${base}.xlsx"`
      );

      res.send(Buffer.from(buf));
    }

  } catch (e) {
    console.error('[export] unexpected error:', e);

    res.status(500).json({
      error: 'The request could not be completed. Please try again.'
    });
  }
});


// ── APPLICATION METADATA ────────────────────────────────────────────────────

// GET /api/meta

app.get('/api/meta', (_req, res) => {
  try {
    const registry = getRegistry();

    const cities = Object.entries(registry.cities || {})
      .map(([key, cfg]) => ({
        key,
        display: cfg.display,
        population: cfg.population || 0,
        data_types: Object.keys(cfg.datasets || {})
          .filter(dt =>
            (cfg.datasets[dt].platform || 'socrata') === 'socrata'
          )
      }))
      .sort((a, b) => b.population - a.population);

    res.json({
      cities,
      data_types: [
        ...new Set(
          Object.values(registry.data_type_aliases || {})
        )
      ],
      trades: Object.keys(registry.trade_keywords || {})
    });

  } catch (e) {
    res.status(500).json({
      error: 'The request could not be completed. Please try again.'
    });
  }
});


// ── START SERVER ────────────────────────────────────────────────────────────

const onListening = () => {
  console.log(`\n${'='.repeat(50)}`);
  console.log(`  StellaScrapes running at http://localhost:${PORT}`);
  console.log(`${'='.repeat(50)}\n`);

  try {
    require('child_process').exec(
      `start http://localhost:${PORT}`
    );
  } catch {
    // Browser launch is optional.
  }
};

app.listen(PORT, HOST, onListening);
