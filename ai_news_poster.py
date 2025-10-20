import os, random, requests, feedparser, datetime

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BLUESKY_USER = os.getenv("BLUESKY_USER")
BLUESKY_PASS = os.getenv("BLUESKY_PASS")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

RSS_FEEDS = [
    "https://www.reddit.com/r/MachineLearning/.rss",
    "https://www.reddit.com/r/ArtificialIntelligence/.rss",
    "https://venturebeat.com/category/ai/feed/",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.analyticsvidhya.com/blog/feed/",
    "https://www.theverge.com/artificial-intelligence/rss/index.xml",
    "https://syncedreview.com/feed/"
]

def fetch_latest_articles(limit=3):
    articles = []
    for feed in RSS_FEEDS:
        d = feedparser.parse(feed)
        for entry in d.entries[:limit]:
            articles.append({"title": entry.title, "link": entry.link})
    random.shuffle(articles)
    return articles[:3]

def summarize_with_groq(title, link):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"Write a short, engaging AI news update (under 280 chars) based on: '{title}'. Add 1 trending #AI hashtag. Include the link {link}."
    data = {"model": "llama-3.1-70b-versatile", "messages": [{"role": "user", "content": prompt}]}
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
    return res.json()["choices"][0]["message"]["content"]

def post_to_bluesky(text):
    if not BLUESKY_USER or not BLUESKY_PASS:
        print("No Bluesky credentials.")
        return
    session = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession",
                            json={"identifier": BLUESKY_USER, "password": BLUESKY_PASS}).json()
    token = session["accessJwt"]
    post_data = {
        "repo": session["did"],
        "collection": "app.bsky.feed.post",
        "record": {"text": text, "createdAt": datetime.datetime.utcnow().isoformat() + "Z"}
    }
    headers = {"Authorization": f"Bearer {token}"}
    requests.post("https://bsky.social/xrpc/com.atproto.repo.createRecord", headers=headers, json=post_data)
    print("✅ Posted to Bluesky")

def post_to_x(text):
    if not TWITTER_BEARER_TOKEN:
        print("No X bearer token.")
        return
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}", "Content-Type": "application/json"}
    data = {"text": text}
    r = requests.post("https://api.twitter.com/2/tweets", headers=headers, json=data)
    print("✅ X:", r.status_code, r.text)

if __name__ == "__main__":
    for art in fetch_latest_articles():
        post_text = summarize_with_groq(art["title"], art["link"])
        print("\n🧠 Generated Post:\n", post_text)
        post_to_bluesky(post_text)
        post_to_x(post_text)
