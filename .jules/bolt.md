# Bolt's Journal - Antel Consumo

## 2025-05-15 - [Scraper Performance Optimization]
**Learning:** Playwright-based scrapers in this codebase were significantly slowed down by waiting for 'networkidle' on a media-heavy site. Blocking non-essential resources (images, fonts, media) and switching to specific element waits reduced the scraping time and resource usage significantly.
**Action:** Always implement resource blocking in scrapers where only text data is needed. Avoid 'networkidle' when specific selectors can be used to signal page readiness.
