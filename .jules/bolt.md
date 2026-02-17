## 2025-05-22 - Performance optimization via resource blocking and direct navigation
**Learning:** Playwright scrapers can be significantly accelerated by blocking non-essential resources (images, fonts, media) and navigating directly to the target URL after login, bypassing intermediate landing pages and UI interactions.
**Action:** Implement `page.route` to block images/fonts/media and optimize the navigation flow to go directly to the consumption page.
