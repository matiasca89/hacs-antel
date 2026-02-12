## 2025-02-12 - Playwright Scraping Optimization
**Learning:** Significant performance gains in text-based scraping are achieved by blocking non-essential resources (images, fonts, media) and using targeted `wait_for_selector` instead of waiting for `networkidle`.
**Action:** Always implement resource routing and element-specific waits in Playwright-based scrapers. Ensure mock objects in test suites are updated to support new browser methods like `route`.
