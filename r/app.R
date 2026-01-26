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
  actionButton("go", "Fetch"),
  tableOutput("results")
)

server <- function(input, output) {
  posts <- eventReactive(input$go, {
    py_to_r(
      fetch_posts$fetch_posts(
        query = input$query,
        instance = "https://mastodon.social",
        count = 10,
        classify = FALSE
      )
    )
  })

  observe({
  print(class(posts()))
  print(str(posts()))
  })

  output$results <- renderTable({
    df <- bind_rows(posts())
    df
  })
}

shinyApp(ui, server)