import asyncio

from automation.surface import BrowserSurface


async def main():
    surface = BrowserSurface()

    try:
        # 1. Open the Member Search page
        await surface.open("http://127.0.0.1:8000")

        # 2. Enter the Member ID
        await surface.fill("Member ID", "12345")

        # 3. Click Search
        await surface.click_text("Search")

        # 4. Open Maya Patel
        await surface.click_text("Maya Patel")

        # 5. Open the Savings account
        await surface.click_text("Savings")

        # 6. Read the final page
        page_text = await surface.read_page()

        print("\n===== FINAL PAGE =====")
        print(page_text)
        print("======================\n")

        # Keep browser open so you can see the result
        input("Press Enter to close the browser...")

    finally:
        await surface.close()


if __name__ == "__main__":
    asyncio.run(main())