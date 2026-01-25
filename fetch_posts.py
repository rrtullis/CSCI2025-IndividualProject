from mastodon import Mastodon
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import datetime
import sqlite3
import torch
import re

# function to fetch latest n posts from an instance
def fetch_posts(query, instance, count):

    # Set up Mastodon client
    mastodon = Mastodon(
        access_token = "c-HY-LRQyxHVEstttE-LFhpEVaW7ai46FloPQyuoDUc",
        api_base_url = instance)

    # Retreive posts (statuses)
    statuses = mastodon.timeline_hashtag(
        hashtag=query,
        limit=count)
    return statuses

def clean_statuses(statuses):
    for status in statuses:
        # Extract post content from HTML
        soup=BeautifulSoup(status['content'], 'html.parser')
        for a in soup.find_all("a", href=True):
            a.replace_with(a.get_text(strip=True))
        content = soup.get_text(separator=" ", strip=True)

        # Remove extra tags at the end of content
        tags=re.finditer(' #', content)
        tags=list(tags)
        if tags:
            status['content'] = content[:tags[-1].start()]
        else:
            status['content'] = content
    return statuses

def classify_statuses(statuses, tokenizer, model):

    status_content=[status['content'] for status in statuses]
    inputs = tokenizer(status_content, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    sentiment_map = {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
    sentiments = [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]
    for i in range(len(statuses)):
        statuses[i]['sentiment'] = sentiments[i]
    return statuses


# Insert into SQLite database - ignore duplicates
def update_posts_db(statuses):

    # set up SQLite connection
    conn = sqlite3.connect("mastodon_posts.db")
    cur = conn.cursor()

    for status in statuses:
        cur.execute("""
            INSERT OR IGNORE INTO posts (id, created_at, query, instance, content, sentiment)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            status["id"],
            status["created_at"],
            query,
            instance,
            status['content'],
            status['sentiment']
        ))

    conn.commit()
    conn.close()

########################################
# sqlite3 setup - the built-in datetime adapter was deprecated

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.replace(tzinfo=None).isoformat()

sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)

def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())

sqlite3.register_converter("datetime", convert_datetime)

########################################

model_name = "tabularisai/multilingual-sentiment-analysis"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

query="privacy"
instance="https://mastodon.social"

results = fetch_posts(query, instance, 10)
results = clean_statuses(results)
results = classify_statuses(results, tokenizer, model)
for r in results:
    print('////\n', r['content'], '\n', r['sentiment'],'\n')
#update_posts_db(results)



# conn = sqlite3.connect("mastodon_posts.db")
# cur = conn.cursor()

# posts = cur.execute("SELECT * FROM posts ORDER BY created_at DESC")
# print(posts.fetchone(), len(posts.fetchall()))


