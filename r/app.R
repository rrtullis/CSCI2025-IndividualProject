library(shiny)
library(bslib)
library(tidyverse)
library(reticulate)
library(shinycssloaders)
library(DT)

# forgot to add conda to PATH, so this is here
Sys.setenv(
  RETICULATE_CONDA = "C:/Users/reaga/miniconda3/Scripts/conda.exe"
)

# load the environment used by fetch_posts
use_condaenv("csci2025ip", required=TRUE)
# 'import' fetch_posts so it can be used here
fetch_posts <- import_from_path(
  "fetch_posts",
  path = "../python"
)

ui <- fluidPage(
  titlePanel("Mastodon Trends Analyzer"),
  sidebarLayout( # the sidebar contains 'global' inputs linked to all tabs' content
    sidebarPanel( 
      textAreaInput( # simplest way I could think of adding optional multiple queries
        "queries",
        "Queries (one per line, up to 5)",
        placeholder = "e.g. cats\nprogramming\ntravel",
        rows = 5
      ),
      numericInput("n","Number of posts to fetch (per query)", value = 10, min = 1, max = 200),
      # sentiment analysis takes extra time, so it is opt-in
      checkboxInput("classify", "Run sentiment analysis?"), 
      checkboxInput("fit_cutoff", "Scale plots to known data?", value=TRUE),
      actionButton("fetch", "Fetch"),
    ),
    mainPanel(
      tabsetPanel(
        tabPanel(
          "Trend Plot", # I had an input I wanted to hide until posts were fetched
          uiOutput("results_plot_ui"), # hence the UI output
        ),
        tabPanel(
          "Sentiment Plot", # the UI outputs also let me make nicer validation text
          uiOutput("results_sentiment_plot_ui") # so each tab has one for consistency
        ),
        tabPanel(
          "Browse Posts",
          uiOutput("results_ui")
        )
      )
    )
  ) 
)

server <- function(input, output) {

  posts <- eventReactive(input$fetch, {
    # split input string into distinct queries
    queries <- strsplit(input$queries, "\n")[[1]] |> 
      trimws() |>
      discard(~ .x == "") |> # drop empty sections
      head(5) # and keep the first five

    if (length(queries > 0)) {
      # get posts for each query
      posts_list <- lapply(queries, function(q) {
      py_to_r(
        fetch_posts$fetch_posts(
          query = q,
          instance = "https://mastodon.social",
          count = input$n,
          classify = input$classify
        )
      )
    })
    # stick em together in a dataframe
    bind_rows(posts_list)
      
    } else { # don't know if I actually need this.
      NULL # just in case, I guess
    }
  })



  cutoff <- reactive({ # this is used for 'zooming' time-based plots to known data
    req(posts())

    cutoff <- posts() |>
    group_by(query) |>
    summarise(earliest = min(created_at), .groups = "drop") |>
    summarise(cutoff = max(earliest)) |>
    pull(cutoff)
  })

  output$results_ui <- renderUI({
    # fetch == 0 ensures validation text is shown initially
    if (input$fetch == 0 || is.null(posts()) || nrow(posts()) == 0) {
      div( # nicer (I think) validation-type content
        style = "
          padding: 2em;
          text-align: center;
          color: #aaa;
        ",
        h4("No data yet"),
        p("Enter one or more queries and click “Fetch” to browse posts.")
      )
    } else {
      tagList(
        withSpinner(dataTableOutput("results"))
      )
    }
  })

  output$show_sentiment_post <- renderDT({
    req(input$show_sentiment_post)
      nearPoints(posts(), input$show_sentiment_post) |>
        select(created_at, query, content, sentiment)
  })

  output$results <- renderDT({
    posts() |>
      select(created_at, query, content, sentiment)
  })

  output$results_plot_ui <- renderUI({

    if (input$fetch == 0 || is.null(posts()) || nrow(posts()) == 0) {
      div(
        style = "
          padding: 2em;
          text-align: center;
          color: #aaa;
        ",
        h4("No data yet"),
        p("Enter one or more queries and click “Fetch” to display trends.")
      )
    } else {
      tagList(
        withSpinner(plotOutput("results_plot", height = 400)),
        numericInput("trends_bin_width", "Bin width (minutes)", value = 15, min=1)
      )
    }
  })

  # one neat thing about Mastodon/its API
  # is that there is no algorithm - posts are shown chronologically
  # so I can reliably fetch the latest n posts and have current information
  # but a downside to this is if you choose two queries with vastly different popularity
  # it can make it look like no one was talking about x until just recently
  # and unfortunately I wasn't able to figure out how to fetch all posts
  # about x and after date y.

  output$results_plot <- renderPlot({
    results_plot <- posts() |>
      ggplot(aes(x=created_at, color=query)) +
      geom_freqpoly(binwidth=input$trends_bin_width * 60) +
      labs(x="Datetime (UTC)", y=("# of posts"), color="Query", title = str_glue("Distribution of the latest {input$n} posts by query")) +
      theme_minimal()
    
    if (input$fit_cutoff) { # ^ which is why we have this option
      results_plot + coord_cartesian(xlim=c(cutoff(), now()))
    } else {
      results_plot
    }
    
  })

  output$results_sentiment_plot_ui <- renderUI({
    if (input$fetch == 0 || is.null(posts()) || nrow(posts()) == 0) {
      div(
        style = "
          padding: 2em;
          text-align: center;
          color: #aaa;
        ",
        h4("No data yet"),
        p("Enter one or more queries and click “Fetch” to display sentiments.")
      )
    } else {
      tagList(
        withSpinner(plotOutput("results_sentiment_plot", height = 400, click="show_sentiment_post")),
        dataTableOutput("show_sentiment_post")
      )
    }
  })

  # disregard previous comment, I changed the plot and added click behavior
  output$results_sentiment_plot <- renderPlot({

    results_sentiment_plot = posts() |>
      mutate(sentiment = factor(sentiment, c("Very Negative", "Negative", "Neutral", "Positive", "Very Positive"))) |>
      ggplot(aes(x=created_at, y = sentiment, color=query)) +
      labs(x="Time Created (UTC)", y="Sentiment", color = "Query", title = str_glue("Sentiment analysis of the latest {input$n} posts by query")) +
      theme_minimal() +
      geom_jitter(width=0, height=0.1, size = 4)

      if (input$fit_cutoff) {
        results_sentiment_plot + coord_cartesian(xlim=c(cutoff(), now()))
      } else {
        results_sentiment_plot
      }
  })

}

shinyApp(ui, server)