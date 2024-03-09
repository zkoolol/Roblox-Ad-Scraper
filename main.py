import asyncio, re, aiohttp, json
from modules.console import Logger

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 429:
                retry_after = response.headers.get('Retry-After', '5')
                Logger.error(f"Ratelimited, retrying after {retry_after} seconds")
                await asyncio.sleep(int(retry_after))
                return await fetch(session, url)
            elif response.status != 200:
                Logger.error(f"Error: {response.status}")
                return None
            return await response.text()
    except aiohttp.ClientError as e:
        Logger.error(f"Error: {e}")
        return None

async def get_ad(session, html, ad_type, webhook_url):
    if html is None:
        return

    ad = re.search(r'<img src="(.*?)" alt="(.*?)"', html)
    if ad:
        ad_image = ad.group(1)
        ad_name = ad.group(2)
        file_type = {1: "banner.txt", 2: "skyscraper.txt", 3: "square.txt"}
        file_path = f"./scraped/{file_type.get(ad_type)}"
        with open(file_path, "a+") as file:
            file.seek(0)
            if ad_image not in file.read():
                file.write(ad_image + "\n")
                type_names = {1: "Banner", 2: "Skyscraper", 3: "Square"}
                type_name = type_names.get(ad_type, "Unknown")
                embed = {
                    "title": "✅ New ad scraped!",
                    "description": "⭐ https://github.com/zkoolol/Roblox-Ad-Scraper",
                    "color": 5763719,
                    "url": ad_image,
                    "image": {"url": ad_image},
                    "fields": [
                        {"name": "Name:", "value": ad_name, "inline": True},
                        {"name": "Type:", "value": type_name, "inline": True}
                    ]
                }

                data = {"embeds": [embed]}
                async with session.post(webhook_url, json=data) as response:
                    if response.status == 204:
                        Logger.info(f"Successfully sent a {type_name.lower()} ad to webhook")
                    else:
                        Logger.error(f"Failed to send ad to webhook | Status Code: {response.status}")

async def main(session, ad_number, webhook_url):
    while True:
        response = await fetch(session, f"https://www.roblox.com/user-sponsorship/{ad_number}")
        if response:
            await get_ad(session, response, ad_number, webhook_url)
        await asyncio.sleep(1)

async def run(config_file):
    with open(config_file) as f:
        config = json.load(f)
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for ad_name, webhook_url in config.items():
            ad_type = {"banner": 1, "skyscraper": 2, "square": 3}.get(ad_name)
            if ad_type is not None:
                tasks.append(main(session, ad_type, webhook_url))
        await asyncio.gather(*tasks)

async def setup(config):
    await run(config)

if __name__ == "__main__":
    config = "config.json"
    asyncio.run(setup(config))