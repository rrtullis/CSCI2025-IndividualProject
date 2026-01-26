from mastodon import Mastodon
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re

# function to fetch latest n posts from an instance
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


    statuses=list(statuses)
    clean_posts = []
    for post in statuses:
        post_dict = {}
        for key, value in post.__dict__.items():
            # Keep only JSON-serializable types
            if isinstance(value, (str, int, float, bool)) or value is None:
                post_dict[key] = value
            else:
                # Replace nested objects with None
                post_dict[key] = "R didn't like this"
        clean_posts.append(post_dict)

    return clean_posts  # list of simple dicts


    # for status in statuses:
    #     status['account'] = status['account']['acct']
    #     del status['mentions']
    #     del status['media_attachments']
    #     del status['emojis']
    #     del status['tags']
    #     del status['filtered']
    #     del status['quote_approval']


    # status_dicts = [status.__dict__ for status in statuses]
    
    # return status_dicts



