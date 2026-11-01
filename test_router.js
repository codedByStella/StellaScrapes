
#!/usr/bin/env node
'use strict';

/**
 * StellaScrapes — Public Release Router Tests
 *
 * Tests the interfaces and functionality retained in the public release.
 *
 * [REDACTED]
 * - Production query parsing test cases.
 * - City and alias matching test matrix.
 * - Dataset-specific registry coverage tests.
 * - Production routing and filtering regression tests.
 * - Live API integration tests.
 */

const {
  route,
  OUTPUT_COLUMNS_BY_TYPE,
  DEFAULT_OUTPUT_COLUMNS,
} = require('../lib/router');

const { getRegistry } = require('../lib/registry');

const PASS = '✓';
const FAIL = '✗';

const results = {
  pass: 0,
  fail: 0,
};

function test(label, fn) {
  try {
    const [ok, message] = fn();

    if (ok) {
      console.log(`  ${PASS}  ${label}: ${message}`);
      results.pass++;
    } else {
      console.log(`  ${FAIL}  ${label}: ${message}`);
      results.fail++;
    }
  } catch (error) {
    console.log(`  ${FAIL}  ${label}: EXCEPTION -- ${error.message}`);
    results.fail++;
  }
}

async function testAsync(label, fn) {
  try {
    const [ok, message] = await fn();

    if (ok) {
      console.log(`  ${PASS}  ${label}: ${message}`);
      results.pass++;
    } else {
      console.log(`  ${FAIL}  ${label}: ${message}`);
      results.fail++;
    }
  } catch (error) {
    console.log(`  ${FAIL}  ${label}: EXCEPTION -- ${error.message}`);
    results.fail++;
  }
}

console.log('\n-- REGISTRY ----------------------------------------------');

test('registry loads', () => {
  const registry = getRegistry();

  return [
    registry !== null &&
      typeof registry === 'object' &&
      !Array.isArray(registry),
    'Registry loaded successfully',
  ];
});

console.log('\n-- OUTPUT SCHEMA -----------------------------------------');

test('output columns available', () => {
  return [
    OUTPUT_COLUMNS_BY_TYPE !== null &&
      typeof OUTPUT_COLUMNS_BY_TYPE === 'object' &&
      Object.keys(OUTPUT_COLUMNS_BY_TYPE).length > 0,
    'Output column definitions are available',
  ];
});

test('output columns have valid structure', () => {
  const invalid = Object.entries(OUTPUT_COLUMNS_BY_TYPE)
    .filter(([, columns]) =>
      !Array.isArray(columns) ||
      !columns.every(column => typeof column === 'string')
    );

  return [
    invalid.length === 0,
    invalid.length === 0
      ? 'All output definitions contain valid column arrays'
      : `Invalid definitions: ${invalid.map(([name]) => name).join(', ')}`,
  ];
});

test('default output columns available', () => {
  return [
    Array.isArray(DEFAULT_OUTPUT_COLUMNS) &&
      DEFAULT_OUTPUT_COLUMNS.length > 0 &&
      DEFAULT_OUTPUT_COLUMNS.every(column => typeof column === 'string'),
    'Default output columns are available',
  ];
});

console.log('\n-- ROUTER INTERFACE --------------------------------------');

async function runRouterTests() {
  await testAsync('route returns result', async () => {
    const result = await route('public release test');

    return [
      result !== null && typeof result === 'object',
      'Router returned a result object',
    ];
  });

  await testAsync('result structure', async () => {
    const result = await route('public release test');

    const requiredFields = [
      'records',
      'query',
      'city',
      'data_type',
      'trade',
      'days',
      'error',
      'count',
    ];

    const missing = requiredFields.filter(
      field => !(field in result)
    );

    return [
      missing.length === 0,
      missing.length === 0
        ? 'Expected result fields are present'
        : `Missing fields: ${missing.join(', ')}`,
    ];
  });

  await testAsync('search reports withheld functionality', async () => {
    const result = await route('public release test');

    return [
      result.error !== null &&
        typeof result.error === 'string' &&
        result.error.length > 0,
      result.error || 'No error message returned',
    ];
  });

  await testAsync('withheld search returns no records', async () => {
    const result = await route('public release test');

    return [
      Array.isArray(result.records) &&
        result.records.length === 0 &&
        result.count === 0,
      'No search results are fabricated or returned',
    ];
  });

  await testAsync('empty query handled', async () => {
    const result = await route('');

    return [
      result.error !== null &&
        result.records.length === 0 &&
        result.count === 0,
      'Empty query returns the public-release unavailable response',
    ];
  });
}

(async () => {
  await runRouterTests();

  console.log('\n-- SUMMARY ------------------------------------------------');

  const total = results.pass + results.fail;

  console.log(`  ${PASS} Passed: ${results.pass}/${total}`);
  console.log(`  ${FAIL} Failed: ${results.fail}/${total}`);

  process.exitCode = results.fail > 0 ? 1 : 0;
})();
