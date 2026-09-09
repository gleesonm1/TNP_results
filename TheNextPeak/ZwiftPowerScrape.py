# from playwright.sync_api import sync_playwright
# import pandas as pd
# from datetime import timedelta
# import json

# ZID = "5344364"

# def fetch_results_playwright(zid):
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page = browser.new_page()

#         # Load *any* ZwiftPower page first to solve Cloudflare
#         page.goto("https://www.zwiftpower.com", timeout=60000)
#         page.wait_for_load_state("networkidle")

#         # Now hit the JSON directly
#         url = f"https://www.zwiftpower.com/cache3/results/{zid}.json"
#         response = page.request.get(url)
#         data = response.json()

#         browser.close()

#     results = []
#     for r in data.get("data", []):
#         raw_time = r[29]
#         formatted_time = (
#             str(timedelta(seconds=int(raw_time)))[2:]
#             if raw_time else "N/A"
#         )
#         results.append({
#             "Rider": r[2],
#             "Category": r[4],
#             "Time": formatted_time
#         })

#     return pd.DataFrame(results)

# df = fetch_results_playwright(ZID)
# print(df.head())
# df.to_csv(f"results_{ZID}.csv", index=False)

# from playwright.sync_api import sync_playwright
# import pandas as pd
# from datetime import timedelta
# import json

# ZID = "5344364"

# def fetch_results_playwright(zid):
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page = browser.new_page()

#         # Step 1: Visit ZwiftPower to establish Cloudflare session
#         page.goto("https://www.zwiftpower.com", timeout=60000)
#         page.wait_for_load_state("networkidle")

#         # Step 2: Fetch JSON from inside the page context
#         url = f"https://www.zwiftpower.com/cache3/results/{zid}.json"

#         response_text = page.evaluate(
#             """async (url) => {
#                 const resp = await fetch(url, { credentials: "include" });
#                 return await resp.text();
#             }""",
#             url
#         )

#         browser.close()

#     # Step 3: Parse JSON safely
#     try:
#         data = json.loads(response_text)
#     except json.JSONDecodeError:
#         print("Response was not JSON. First 500 chars:")
#         print(response_text[:500])
#         raise

#     results = []
#     for r in data.get("data", []):
#         raw_time = r[29]
#         formatted_time = (
#             str(timedelta(seconds=int(raw_time)))[2:]
#             if raw_time else "N/A"
#         )
#         results.append({
#             "Rider": r[2],
#             "Category": r[4],
#             "Time": formatted_time
#         })

#     return pd.DataFrame(results)

from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import timedelta
import json
from pathlib import Path

ZID = "5344364"
OUTFILE = Path(f"results_{ZID}.csv")

def fetch_results_playwright(zid):
    json_url_fragment = f"/cache3/results/{zid}.json"
    json_body = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Capture the JSON response when ZwiftPower loads it
        def handle_response(response):
            nonlocal json_body
            if json_url_fragment in response.url and response.status == 200:
                json_body = response.text()

        page.on("response", handle_response)

        # Load the EVENT PAGE and let ZwiftPower fetch its own data
        event_url = f"https://www.zwiftpower.com/events.php?zid={zid}"
        page.goto(event_url, timeout=60000)
        page.wait_for_load_state("networkidle")

        browser.close()

    if json_body is None:
        raise RuntimeError("ZwiftPower JSON was never requested by the page")

    data = json.loads(json_body)

    # Build dataframe
    results = []
    for r in data.get("data", []):
        raw_time = r[29]
        formatted_time = (
            str(timedelta(seconds=int(raw_time)))[2:]
            if raw_time else "N/A"
        )
        results.append({
            "Rider": r[2],
            "Category": r[4],
            "Time": formatted_time,
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = fetch_results_playwright(ZID)

    if df.empty:
        print("⚠️ No results found — CSV not written.")
    else:
        df.to_csv(OUTFILE, index=False)
        print(f"✅ Wrote {len(df)} rows to {OUTFILE.resolve()}")






