from mastodon import Mastodon
from bs4 import BeautifulSoup
import datetime
import sqlite3
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
    # Get plaintext post content
    for status in statuses:
        content=''
        soup=BeautifulSoup(status['content'], 'html.parser')
        all_tags=soup.find_all()
        for tag in all_tags:
            content+= tag.get_text()

        # Remove extra tags at the end of content
        tags=re.finditer(' #', content)
        tags=list(tags)
        if tags:
            status['content'] = content[:tags[-1].start()]
        else:
            pass
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
            "PLACEHOLDER"
        ))

    conn.commit()
    conn.close()

########################################
# sqlite3 setup - the built-in datetime adapter was deprecated

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.replace(tzinfo=None).isoformat()
3
sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)

def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.datetime.fromisoformat(val.decode())

sqlite3.register_converter("datetime", convert_datetime)

########################################

query="ai"
instance="https://mastodon.social"

results = fetch_posts(query, instance, 5)
results = clean_statuses(results)
update_posts_db(results)

conn = sqlite3.connect("mastodon_posts.db")
cur = conn.cursor()

posts = cur.execute("SELECT * FROM posts")
print(posts.fetchall()[-1])



