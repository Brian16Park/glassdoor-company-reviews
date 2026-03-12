import requests

url = "https://www.wikidata.org/w/api.php"
params = {
    "action": "wbsearchentities",
    "search": "Google",
    "language": "en",
    "format": "json",
    "limit": 1
}

r = requests.get(url, params=params, timeout=15)

print("STATUS:", r.status_code)
print("CONTENT-TYPE:", r.headers.get("Content-Type"))
print("TEXT:", r.text[:500])