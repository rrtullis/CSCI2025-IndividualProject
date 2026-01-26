import pandas as pd
import matplotlib.pyplot as plt
from shiny.express import input, render, ui
from fetch_posts import fetch_posts


ui.page_opts(title="Mastodon Posts Analysis")
with ui.nav_panel("Trends"):  
    ui.h2("Analysis of trends")
    ui.input_text("trends_query", "Search query")
    ui.input_numeric("trends_n", "Number of posts", value=50, min=10, max=200)
    ui.input_numeric("trends_bin", "Bin size (minutes)", value=15, min=1)

    @render.plot
    def trends_plot():
        query=input.trends_query()
        n=input.trends_n()
        bin_minutes=input.trends_bin()

        if not query:
            return
        
        posts = fetch_posts(query, 'https://mastodon.social', n)

        if not posts:
            return
        
        df = pd.DataFrame(posts)
        # make timestamps usable
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)

        # floor timestamps into bins
        bin_rule = f"{bin_minutes}min"
        df["time_bin"] = df["created_at"].dt.floor(bin_rule)

        # count posts per bin
        counts = (
            df.groupby("time_bin")
            .size()
            .reset_index(name="count")
            .sort_values("time_bin")
        )

        # plot frequency polygon
        fig, ax = plt.subplots()
        ax.plot(counts["time_bin"], counts["count"], marker="o")

        ax.set_title(f"Post frequency for '{query}'")
        ax.set_xlabel("Time")
        ax.set_ylabel("Number of posts")

        fig.autofmt_xdate()
        return fig

with ui.nav_panel("Sentiment"):  
    "Analysis of sentiment"
    ui.input_text("sentiment_query", "Search query")
    @render.text
    def text_sentiment_query():
        return input.sentiment_query()

