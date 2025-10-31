import re
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(
    title="NGYT777GG Vehicle Info API",
    description="🚗 Vehicle Info Extractor by @NGYT777GG | Vercel Edition",
    version="1.0"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36",
    "Referer": "https://vahanx.in/",
    "Accept-Language": "en-US,en;q=0.9"
}


def fetch_html(rc: str):
    url = f"https://vahanx.in/rc-search/{rc}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def section_blocks(soup):
    blocks = {}
    for h3 in soup.find_all("h3"):
        parent = h3.find_parent("div", class_="hrc-details-card")
        if parent:
            blocks[h3.text.strip()] = parent
    return blocks


def parse_block(block):
    data = {}
    for span in block.find_all("span"):
        label = span.text.strip()
        val_tag = span.find_next("p")
        if label and val_tag:
            value = val_tag.text.strip()
            data[label] = value
    return data


def extract_all(soup):
    result = {}
    for header, blk in section_blocks(soup).items():
        result[header] = parse_block(blk)
    top = {}
    for div in soup.select(".hrcd-cardbody"):
        s = div.find("span")
        p = div.find("p")
        if s and p:
            top[s.text.strip()] = p.text.strip()
    if top:
        result["Basic Card Info"] = top
    return result


def scrape_vehicle(rc: str):
    try:
        soup = fetch_html(rc)
    except Exception as e:
        return {"error": f"❌ Unable to fetch data: "}

    data = extract_all(soup)
    reg = soup.find("h1")
    if reg:
        data["registration_number"] = reg.text.strip()

    box = soup.select_one(".insurance-alert-box.expired .title")
    if box:
        m = re.search(r"(\d+)", box.text)
        if m:
            data.setdefault("Insurance Alert", {})["Expired Days"] = m.group(1)
    return data


@app.get("/")
def home():
    return {
        "message": "🚗 Welcome to NGYT777GG VEHICLE INFO API",
        "usage": "/lookup?rc=MH12DE1433",
        "author": "@NGYT777GG"
    }


@app.get("/lookup")
def lookup(rc: str = Query(..., description="Vehicle Registration Number")):
    data = scrape_vehicle(rc)
    if "error" in data:
        return JSONResponse(content=data, status_code=400)
    return JSONResponse(content=data)
