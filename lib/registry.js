
'use strict';

/**
 * Loads the application registry from the project root.
 */

const fs = require('fs');
const path = require('path');

const REGISTRY_PATH = path.join(__dirname, '..', 'registry.json');

function getRegistry() {
  const raw = fs.readFileSync(REGISTRY_PATH, 'utf8');
  return JSON.parse(raw);
}

module.exports = { getRegistry, REGISTRY_PATH };
