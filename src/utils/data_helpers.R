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