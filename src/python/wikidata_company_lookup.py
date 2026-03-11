import re
import pandas as pd
import requests
import time
from pathlib import Path

session = requests.Session()
session.headers.update({
    "User-Agent": "glassdoor-company-reviews/1.0 (roddur99@gmail.com)"
})

output_dir = Path("data/company_tagger")
output_dir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv("data/raw/glassdoor-companies-reviews.csv")
companies = pd.Series(df["company_name"].dropna().unique(), name="company_name")

abbreviation_map = {
    "TD": "Toronto-Dominion Bank",
    "RBC": "Royal Bank of Canada"
}

def normalize_company(name):
    name = str(name).strip()
    name = re.sub(r"[^\w\s]", "", name)

    suffixes = [
        "inc", "llc", "ltd", "corp", "corporation",
        "co", "company", "group", "holdings",
        "plc", "lp", "limited"
    ]

    tokens = name.split()
    tokens = [t for t in tokens if t.lower() not in suffixes]

    return " ".join(tokens).strip()

def get_wikipedia_title(company):

    url = "https://en.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "list": "search",
        "srsearch": company,
        "format": "json",
        "srlimit": 5
    }

    r = session.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    results = data.get("query", {}).get("search", [])

    if not results:
        return None

    company_lower = company.lower()

    for result in results:
        title = result["title"]
        snippet = result.get("snippet", "").lower()

        if company_lower in title.lower() or company_lower in snippet:
            return title

    return results[0]["title"]

def get_qid_from_wikipedia(title):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageprops",
        "format": "json"
    }

    r = session.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        pageprops = page.get("pageprops", {})
        if "wikibase_item" in pageprops:
            return pageprops["wikibase_item"]

    return None

def get_industry(qid):
    url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

    r = session.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    try:
        claims = data["entities"][qid]["claims"]["P452"]
        industry_id = claims[0]["mainsnak"]["datavalue"]["value"]["id"]

        label_url = f"https://www.wikidata.org/wiki/Special:EntityData/{industry_id}.json"
        label_data = session.get(label_url, timeout=10)
        label_data.raise_for_status()
        label_data = label_data.json()

        return label_data["entities"][industry_id]["labels"]["en"]["value"]
    except Exception:
        return None

lookup_rows = []
found_count = 0
missing_count = 0
total = len(companies)

for i, company in enumerate(companies, start=1):
    try:
        print(f"[{i}/{total}] Probing: {company}")

        search_name = abbreviation_map.get(company, company)

        wiki_title = get_wikipedia_title(search_name)
        match_method = "wikipedia" if wiki_title else None

        if not wiki_title:
            cleaned = normalize_company(search_name)
            wiki_title = get_wikipedia_title(cleaned)
            match_method = "normalized_wikipedia" if wiki_title else None

        qid = get_qid_from_wikipedia(wiki_title) if wiki_title else None
        industry = get_industry(qid) if qid else None

        if industry is not None:
            found_count += 1
        else:
            missing_count += 1

        lookup_rows.append({
            "company_name": company,
            "industry": industry,
            "match_method": match_method,
            "wiki_title": wiki_title,
            "qid": qid
        })

        print(f"[{i}/{total}] Appended: {industry}")
        time.sleep(0.5)

    except Exception as e:
        print(f"[{i}/{total}] Error for {company}: {e}")
        lookup_rows.append({
            "company_name": company,
            "industry": None,
            "match_method": None,
            "wiki_title": None,
            "qid": None
        })
        missing_count += 1

lookup_df = pd.DataFrame(lookup_rows)
df = df.merge(lookup_df[["company_name", "industry"]], on="company_name", how="left")

lookup_df.to_csv(output_dir / "company_industry_lookup.csv", index=False)

missing = lookup_df[lookup_df["industry"].isna()]
missing.to_csv(output_dir / "missing_industries.csv", index=False)

df.to_csv(output_dir / "glassdoor_companies_tagged.csv", index=False)

missing_ranked = (
    df[df["industry"].isna()]["company_name"]
    .value_counts()
    .reset_index()
)

missing_ranked.columns = ["company_name", "review_count"]
missing_ranked.to_csv(output_dir / "missing_industries_ranked.csv", index=False)

print("Company tagging complete.")
print("Total review rows:", len(df))
print("Unique companies:", len(lookup_df))
print("Industries found:", found_count)
print("Missing industries:", missing_count)