from mastodon import Mastodon
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re

# function to fetch latest n posts from an instance
# it is horribly inefficient but it works. I will redo it if I have time later.
def fetch_posts(query, instance, count, classify = False):

    # Set up Mastodon client
    mastodon = Mastodon(
        access_token = "c-HY-LRQyxHVEstttE-LFhpEVaW7ai46FloPQyuoDUc",
        api_base_url = instance)

    # Retreive posts (statuses)
    statuses = mastodon.timeline_hashtag(
        hashtag=query,
        limit=count)

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

        # safety net
        if not classify:
            status['sentiment'] = 'NA'

    # classify status sentiment
    if classify:
        # params for classification procedure
        model_name = "tabularisai/multilingual-sentiment-analysis"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)

        # get and tokenize inputs
        status_content=[status['content'] for status in statuses]
        inputs = tokenizer(status_content, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        # classify and map into categorical score
        with torch.no_grad():
            outputs = model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        sentiment_map = {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
        sentiments = [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]
        
        # update statuses with new key-value pair
        for i in range(len(statuses)):
            statuses[i]['sentiment'] = sentiments[i]

    # stuff to make it possible to get these into R
    # (clean up later)
    statuses=list(statuses)
    clean_statuses = []
    for status in statuses:
        status_dict = {}
        for key, value in status.__dict__.items():
            # Keep only JSON-serializable types
            if isinstance(value, (str, int, float, bool)) or value is None or key == 'created_at': # the dates are stored in an odd way
                status_dict[key] = value
            else:
                # Replace nested objects with placeholder
                status_dict[key] = "R didn't like this"
        clean_statuses.append(status_dict)

    return clean_statuses  # list of simple dicts





