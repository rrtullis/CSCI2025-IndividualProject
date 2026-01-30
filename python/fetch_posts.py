from mastodon import Mastodon
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re

def fetch_posts(queries, instance, count, classify = False):
    # handle single query
    if type(queries) is not list:
        queries = [queries]

    # Set up Mastodon client
    mastodon = Mastodon(
        access_token = "c-HY-LRQyxHVEstttE-LFhpEVaW7ai46FloPQyuoDUc",
        api_base_url = instance)

    # Set up LLM
    if classify:
        model_name = "tabularisai/multilingual-sentiment-analysis"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)

    # get combined list of statuses
    all_statuses = []
    for query in queries:
        # Retreive posts (statuses)
        statuses = mastodon.timeline_hashtag(
        hashtag=query,
        limit=count)

        # add query attribute & sentiment safety net
        # TODO: find a way to avoid nested iteration
        for status in statuses:
            status['query'] = query
            if not classify:
                status['sentiment'] = 'NA'

        all_statuses += statuses

    # convert to Python default types & parse HTML content
    all_statuses = list(all_statuses)
    clean_statuses = []
    for status in all_statuses:
        # convert Mastodon objects to Python dictionaries
        status_dict = {}
        for key, value in status.__dict__.items():
            # Keep only JSON-serializable types
            if isinstance(value, (str, int, float, bool)) or value is None or key == 'created_at': # the dates are stored in an odd way
                status_dict[key] = value
            else:
                # Replace nested objects with placeholder
                status_dict[key] = "FIX LATER"

        # Extract post content from HTML
        soup=BeautifulSoup(status_dict['content'], 'html.parser')
        for a in soup.find_all("a", href=True):
            a.replace_with(a.get_text(strip=True))
        content = soup.get_text(separator=" ", strip=True)

        # Remove extra tags at the end of content
        tags=re.finditer(' #', content)
        tags=list(tags)
        if tags:
            status_dict['content'] = content[:tags[-1].start()]
        else:
            status_dict['content'] = content

        clean_statuses.append(status_dict)

    if classify:
        # get and tokenize inputs
        status_content=[status['content'] for status in clean_statuses]
        inputs = tokenizer(status_content, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        # classify and map into categorical score
        with torch.no_grad():
            outputs = model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
        sentiment_map = {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
        sentiments = [sentiment_map[p] for p in torch.argmax(probabilities, dim=-1).tolist()]
        
        # update statuses with new key-value pair
        for i in range(len(clean_statuses)):
            clean_statuses[i]['sentiment'] = sentiments[i]

    return clean_statuses

###
results = fetch_posts(["ai", "cats"], "https://mastodon.social", 20)
for r in results:
    print(r['content'][:10], '\n', r['sentiment'])
