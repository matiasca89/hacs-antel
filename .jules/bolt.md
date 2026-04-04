## 2024-05-22 - [Scraper Performance Optimization]
**Learning:** Playwright scrapers can be significantly accelerated by blocking non-essential assets (images, fonts, media) and bypassing redundant UI interactions via direct navigation to target URLs. Replacing broad `networkidle` waits with specific `wait_for_selector` calls further reduces idle time.
**Action:** Always implement resource blocking and direct navigation when possible in Playwright-based scrapers. Prefer `wait_for_selector` over `networkidle` or `asyncio.sleep`.
