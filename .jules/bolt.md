# Bolt's Performance Journal

## 2025-05-22 - Optimized Antel Scraper with Resource Blocking and Targeted Waits
**Learning:** Generic `networkidle` waits and hardcoded `sleep` calls are common bottlenecks in scrapers. Blocking non-essential assets (images, fonts, media) not only saves bandwidth but also makes `networkidle` trigger much faster or even unnecessary.
**Action:** Always prefer `wait_for_selector` for critical content over `networkidle` + `sleep`. Implement `page.route` to block unneeded heavy assets in Playwright scrapers.
