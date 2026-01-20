"""Script to inspect Antel login page and get selectors."""
import asyncio
from playwright.async_api import async_playwright


async def inspect_antel_page():
    """Navigate to Antel page and get HTML structure."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print("Navigating to Antel page...")
        await page.goto(
            "https://aplicaciones.antel.com.uy/miAntel/consumo/internet",
            wait_until="networkidle",
            timeout=60000
        )

        print(f"\nCurrent URL: {page.url}")
        print(f"Page title: {await page.title()}")

        # Get all input elements
        print("\n=== INPUT ELEMENTS ===")
        inputs = await page.query_selector_all("input")
        for inp in inputs:
            inp_type = await inp.get_attribute("type") or "text"
            inp_name = await inp.get_attribute("name") or ""
            inp_id = await inp.get_attribute("id") or ""
            inp_class = await inp.get_attribute("class") or ""
            inp_placeholder = await inp.get_attribute("placeholder") or ""
            print(f"  type={inp_type}, name={inp_name}, id={inp_id}, class={inp_class}, placeholder={inp_placeholder}")

        # Get all buttons
        print("\n=== BUTTONS ===")
        buttons = await page.query_selector_all("button")
        for btn in buttons:
            btn_type = await btn.get_attribute("type") or ""
            btn_id = await btn.get_attribute("id") or ""
            btn_class = await btn.get_attribute("class") or ""
            btn_text = await btn.text_content() or ""
            print(f"  type={btn_type}, id={btn_id}, class={btn_class}, text={btn_text.strip()[:50]}")

        # Get all forms
        print("\n=== FORMS ===")
        forms = await page.query_selector_all("form")
        for form in forms:
            form_id = await form.get_attribute("id") or ""
            form_class = await form.get_attribute("class") or ""
            form_action = await form.get_attribute("action") or ""
            print(f"  id={form_id}, class={form_class}, action={form_action}")

        # Get all links
        print("\n=== LINKS (first 10) ===")
        links = await page.query_selector_all("a")
        for link in links[:10]:
            link_href = await link.get_attribute("href") or ""
            link_text = await link.text_content() or ""
            print(f"  href={link_href}, text={link_text.strip()[:50]}")

        # Save screenshot
        await page.screenshot(path="antel_page.png", full_page=True)
        print("\nScreenshot saved to antel_page.png")

        # Save HTML
        html = await page.content()
        with open("antel_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML saved to antel_page.html")

        # Print portion of HTML for context
        print("\n=== HTML BODY (first 3000 chars) ===")
        print(html[:3000])

        await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_antel_page())
