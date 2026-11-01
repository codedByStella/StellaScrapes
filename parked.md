
# Known Limitations

This document tracks intentionally deferred functionality and current platform limitations. Items should only be removed once the corresponding functionality has been implemented and verified.

---

## 1. Business prospect discovery is deferred

**Status:** Blocked

The current business-listing integration does not reliably retrieve listing data because the upstream service restricts automated requests.

The feature remains deferred pending a reliable and appropriately authorized data source.

**What remains:**
- Select and integrate a suitable business-data provider.
- Distinguish upstream access restrictions from genuine zero-result searches.
- Verify reliable retrieval before restoring the workflow.

---

## 2. Additional data platforms lack fetch implementations

**Status:** Partially implemented

The registry contains configurations for multiple data platforms, but only a subset currently has working retrieval support.

Unsupported platforms are identified rather than presented as operational.

**What remains:**
- Implement and test additional platform adapters.
- Maintain consistent behavior across the Python and Node.js interfaces.
- Verify platform compatibility before enabling each integration.

---

*These limitations were identified during a full-pipeline engineering audit. They remain documented intentionally rather than being represented as completed functionality.*
