# Missing Check Function
Missing.Check.By.Column <- function(df){
  return (apply(is.na(df), 2, sum))
}