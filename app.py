from shiny.express import input, render, ui

ui.page_opts(title="Mastodon Posts Analysis")
with ui.nav_panel("Trends"):  
    "Analysis of trends"
    ui.input_text("trends_query", "Search query")
    @render.text
    def text_trends_query():
        return input.trends_query()

with ui.nav_panel("Sentiment"):  
    "Analysis of sentiment"
    ui.input_text("sentiment_query", "Search query")
    @render.text
    def text_sentiment_query():
        return input.sentiment_query()

