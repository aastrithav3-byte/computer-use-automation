from pathlib import Path

from playwright.async_api import Page


class BrowserSurface:
    """
    Gives our automation system a simple interface
    for interacting with a web browser.
    """

    def __init__(self, page: Page):
        self.page = page

    async def open(self, url: str):
        await self.page.goto(url)

    async def click_text(self, text: str) -> bool:
        """
        Click an element containing the exact text.

        Returns:
            True  -> element existed and was clicked
            False -> element was not found
        """
        locator = self.page.get_by_text(
            text,
            exact=True,
        )

        count = await locator.count()

        if count == 0:
            return False

        await locator.first.click()

        return True

    async def fill_label(
        self,
        label: str,
        value: str,
    ):
        await self.page.get_by_label(label).fill(value)

    async def read_page(self) -> str:
        return await self.page.locator("body").inner_text()

    async def screenshot(self, path: str):
        Path(path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        await self.page.screenshot(
            path=path,
            full_page=True,
        )