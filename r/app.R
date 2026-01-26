library(shiny)
library(bslib)
library(tidyverse)
library(reticulate)

Sys.setenv(
  RETICULATE_CONDA = "C:/Users/reaga/miniconda3/Scripts/conda.exe"
)
use_condaenv("csci2025ip", required=TRUE)

fetch_posts <- import_from_path(
  "fetch_posts",
  path = "../python"
)

ui <- fluidPage(
  textInput("query", "Query"),
  numericInput("n","Number of posts", value = 10, min = 1, max = 200),
  checkboxInput("classify", "Run sentiment analysis?"),
  actionButton("go", "Fetch"),
  tableOutput("results")
)

server <- function(input, output) {
  posts <- eventReactive(input$go, {
    py_to_r(
      fetch_posts$fetch_posts(
        query = input$query,
        instance = "https://mastodon.social",
        count = input$n,
        classify = input$classify
      )
    )
  })

  output$results <- renderTable({
    bind_rows(posts()) |>
      select(created_at, content, sentiment)

  })
}

shinyApp(ui, server)