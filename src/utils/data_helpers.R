# Missing Check Function
Missing.Check.By.Column <- function(df) {
  sapply(df, function(x) {
    if (is.character(x)) {
      sum(is.na(x) | trimws(x) == "")
    } else {
      sum(is.na(x))
    }
  })
}

# Returns Missing Summary in descending order
Missing.Summary <- function(df) {
  missing_counts <- sapply(df, function(x) {
    if (is.character(x)) {
      sum(is.na(x) | trimws(x) == "")
    } else {
      sum(is.na(x))
    }
  })
  
  missing_counts_sorted <- sort(missing_counts, decreasing = TRUE)
  
  data.frame(
    column = names(missing_counts_sorted),
    missing = missing_counts_sorted,
    percent = round(missing_counts_sorted / nrow(df) * 100, 2),
    row.names = NULL
  )
}

## Column Removing Function
Remove.Columns <- function(df, cols) {
  existing <- intersect(cols, names(df))
  missing  <- setdiff(cols, names(df))
  
  if (length(missing) > 0) {
    message("Columns not found: ", paste(missing, collapse = ", "))
  }
  
  if (length(existing) > 0) {
    message("Columns removed: ", paste(existing, collapse = ", "))
  }
  
  df[, !(names(df) %in% cols), drop = FALSE]
}

## Trim white space and default empty cells to NA across dataframe
Clean.Whitespace.NA <- function(df) {
  df %>%
    mutate(across(
      where(is.character),
      ~ {
        x <- trimws(.)
        na_if(x, "")
      }
    ))
}