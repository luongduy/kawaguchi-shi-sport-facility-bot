import asyncio
import requests
import os
from playwright.async_api import async_playwright, Frame
from datetime import datetime, timedelta
import re


async def send_slack_message(webhook_url: str, message: str):
    """
    Send a message to Slack using a webhook URL.

    Args:
        webhook_url (str): The Slack webhook URL
        message (str): The message to send

    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        payload = {
            "text": message,
            "username": "Sports Facility Bot",
            "icon_emoji": ":sports_medal:",
        }

        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Message sent to Slack successfully!")
            return True
        else:
            print(
                f"❌ Failed to send message to Slack. Status code: {response.status_code}"
            )
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending message to Slack: {e}")
        return False


async def check_for_taikukan(frame: Frame, name: str, order: int, day_of_week: str):
    match day_of_week:
        case "sat":
            day_of_week = 5
        case "sun":
            day_of_week = 6
        case "wed":
            day_of_week = 2
        case _:
            day_of_week = int(day_of_week)

    print(f"Checking {name} on {day_of_week}...")

    # Click 予約 button next to 芝スポーツセンター
    await frame.wait_for_selector(
        f"xpath=//tr[td[contains(text(), '{name}')]]//input[@alt='予約画面へ']"
    )

    await frame.locator(
        f"xpath=//td[contains(text(), '{name}')]/preceding-sibling::td//input[@alt='予約画面へ']"
    ).nth(order).click()
    await frame.wait_for_timeout(3000)

    # Go to next month if needed
    today = datetime.today()

    # Get the next target day (skip today if today is target day)
    if today.weekday() == day_of_week:
        next_target_day = today + timedelta(days=7)
    else:
        days_until_target_day = (day_of_week - today.weekday()) % 7
        next_target_day = today + timedelta(days=days_until_target_day)

    # Get the month displayed in the calendar
    calendar_title = await frame.locator("#hdYM").inner_text()
    calendar_year_month = datetime.strptime(calendar_title.strip(), "%Y年%m月")

    # Click "next month" only if the next target day is in a different month
    if (calendar_year_month.year, calendar_year_month.month) != (
        next_target_day.year,
        next_target_day.month,
    ):
        await frame.locator(
            "xpath=//th[@class='clsCalTitle1']//img[@alt='翌月表示']"
        ).click()
        await frame.wait_for_timeout(3000)

    # Click the next target day on the calendar
    next_target_day_str = next_target_day.strftime("%Y%m%d")
    await frame.locator(f"a[href*='set_data({next_target_day_str})']").click()
    await frame.wait_for_timeout(3000)

    # Find the row that contains the text "体育館"
    taiikukan_row = frame.locator("tr", has_text="体育館").first

    # Within that row, find all img tags with alt="予約可能"
    available_slots = await taiikukan_row.locator("img[alt='予約可能']").all()

    if available_slots:
        return True, next_target_day_str
    else:
        return False, next_target_day_str


async def check_for_second_taikukan(frame: Frame, name: str):
    await frame.select_option('select[name="lst_kaikan"]', label=name)
    await frame.evaluate(
        'document.querySelector("select[name=lst_kaikan]").dispatchEvent(new Event("change"))'
    )
    await frame.wait_for_timeout(5000)

    print(f"Checking {name}...")

    # Find the row that contains the text "体育館"
    taiikukan_row = frame.locator("tr", has_text=re.compile("体育館|アリーナ")).last

    if not taiikukan_row:
        return f"{name}: No available slots."

    # Within that row, find all img tags with alt="予約可能"
    available_slots = await taiikukan_row.locator("img[alt='予約可能']").all()

    if available_slots:
        return True
    else:
        return False


async def run(slack_webhook_url: str = None, headless: bool = True):
    async with async_playwright() as p:
        # Capture the execution time
        execution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()

        # Step 1: Go to the main page with frameset
        await page.goto(
            "https://www.pa-reserve.jp/eap-rj/rsv_rj/core_i/init.asp?KLCD=112039&SBT=1&Target=_Top&LCD="
        )

        # Step 1.5: Wait for the MainFrame to load
        await page.wait_for_load_state("domcontentloaded")
        frame = page.frame(name="MainFrame")
        if not frame:
            print("MainFrame not found!")
            await browser.close()
            return

        # Step 2: Click 分類 button
        await frame.wait_for_selector("input[alt='分類']")
        await frame.click("input[alt='分類']")

        # Step 3: Check スポーツ施設 checkbox
        await frame.wait_for_selector("input[id='00003']")
        await frame.check("input[id='00003']")

        # Step 4: Click 所在地を指定せずに検索 button
        await frame.wait_for_timeout(1000)
        await frame.wait_for_selector("input[alt='所在地を指定せずに検索']")
        await frame.click("input[alt='所在地を指定せずに検索']")
        await page.wait_for_load_state("domcontentloaded")

        # Step 5: Click 予約 button next to 芝スポーツセンター
        await frame.wait_for_selector(
            "xpath=//tr[td[contains(text(), '芝スポーツセンター')]]//input[@alt='予約画面へ']"
        )

        await frame.locator(
            "xpath=//td[contains(text(), '芝スポーツセンター')]/preceding-sibling::td//input[@alt='予約画面へ']"
        ).last.click()

        result, next_target_day_str = await check_for_taikukan(
            frame, "芝スポーツセンター", 1, "sat"
        )

        data = {
            "芝スポーツセンター": result,
        }

        # Step 6: Check for other sports facilities
        next_taikukan = [
            "体育武道センター",
            "鳩ヶ谷スポーツセンター",
            "戸塚スポーツセンター",
            "西スポーツセンター",
            "安行スポーツセンター",
            "東スポーツセンター",
        ]

        for taikukan in next_taikukan:
            result = await check_for_second_taikukan(frame, taikukan)
            data[taikukan] = result

        if any(data.values()):
            next_target_day_str = datetime.strptime(
                next_target_day_str, "%Y%m%d"
            ).strftime("%Y-%m-%d")
            msg = f"✅✅✅🏃‍♂️ Sports Facilities Available for {next_target_day_str}:\n"
            msg += f"🕒 Checked at: {execution_time}\n\n"
            for key, value in data.items():
                if value:
                    msg += f"✅ {key}: Available\n"
                else:
                    msg += f"❌ {key}: Not available\n"

            print(msg)

            # Send to Slack if webhook URL is provided
            if slack_webhook_url:
                await send_slack_message(slack_webhook_url, msg)
        else:
            msg = f"🕒 Checked at: {execution_time}\n"
            msg += "❌ No available slots found for any sports facilities."
            print(msg)

            # Send to Slack if webhook URL is provided
            if slack_webhook_url:
                await send_slack_message(slack_webhook_url, msg)

        # Only prompt for input when running locally (not headless)
        if not headless:
            input("Press Enter to continue...")

        await browser.close()


if __name__ == "__main__":
    # Get Slack webhook URL from environment variable
    slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    # Check if running in GitHub Actions or locally
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

    if is_github_actions:
        # Running in GitHub Actions - use headless mode
        asyncio.run(run(slack_webhook_url, headless=True))
    else:
        # Running locally - you can choose headless mode or not
        # For local development, you might want to see the browser
        asyncio.run(run(slack_webhook_url, headless=False))
