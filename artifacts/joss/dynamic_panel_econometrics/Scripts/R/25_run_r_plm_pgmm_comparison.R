# Artifact 25: R cross-software dynamic-GMM comparison
# Comparator: plm::pgmm
#
# Input:
#   Data/Processed/22_dynamic_gmm_controlled_panel.csv
#
# Outputs:
#   Artifacts/Joss/tables/25_cross_software_comparison/25_r_plm_difference_gmm_results.csv
#   Artifacts/Joss/tables/25_cross_software_comparison/25_r_plm_system_gmm_results.csv
#   Artifacts/Joss/tables/25_cross_software_comparison/25_r_plm_run_log.csv

required <- c("plm")

for (pkg in required) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

library(plm)

root <- "C:/Users/omoko/OneDrive/Papers/Dynamic_Panel_Econometrics"
setwd(root)

outdir <- file.path(root, "Artifacts/Joss/tables/25_cross_software_comparison")
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

data_path <- file.path(root, "Data/Processed/22_dynamic_gmm_controlled_panel.csv")
df <- read.csv(data_path)

required_cols <- c("id", "time", "y", "x_pred", "x_exog", "L1_y")
missing_cols <- setdiff(required_cols, names(df))
if (length(missing_cols) > 0) {
  stop(paste("Missing required columns:", paste(missing_cols, collapse = ", ")))
}

df$id <- as.integer(df$id)
df$time <- as.integer(df$time)

pdata <- pdata.frame(df, index = c("id", "time"))

tidy_pgmm <- function(model, model_name) {
  s <- summary(model, robust = TRUE)

  coefs <- as.data.frame(s$coefficients)
  coefs$term <- rownames(coefs)
  rownames(coefs) <- NULL

  names(coefs) <- make.names(names(coefs))

  # plm usually gives Estimate, Std..Error, z.value, Pr...z..
  estimate_col <- grep("Estimate", names(coefs), value = TRUE)[1]
  se_col <- grep("Std", names(coefs), value = TRUE)[1]
  stat_col <- grep("z|t", names(coefs), value = TRUE, ignore.case = TRUE)[1]
  p_col <- grep("Pr", names(coefs), value = TRUE)[1]

  out <- data.frame(
    model = model_name,
    package = "plm",
    term = coefs$term,
    coefficient = as.numeric(coefs[[estimate_col]]),
    std_error = as.numeric(coefs[[se_col]]),
    statistic = as.numeric(coefs[[stat_col]]),
    p_value = as.numeric(coefs[[p_col]]),
    stringsAsFactors = FALSE
  )

  out$term_norm <- out$term
  out$term_norm <- gsub("lag\\(y, 1\\)", "L1_y", out$term_norm, fixed = FALSE)
  out$term_norm <- gsub("\\(Intercept\\)", "const", out$term_norm)

  out
}

run_log <- data.frame(
  model = character(),
  status = character(),
  message = character(),
  stringsAsFactors = FALSE
)

# Difference GMM
# Equivalent intent:
# y_it = rho*y_i,t-1 + beta1*x_pred_it + beta2*x_exog_it + error
# GMM-style: lag(y, 2:3), lag(x_pred, 2:3)
# IV-style: x_exog
diff_result <- tryCatch({
  pgmm(
    y ~ lag(y, 1) + x_pred + x_exog |
      lag(y, 2:3) + lag(x_pred, 2:3) + x_exog,
    data = pdata,
    effect = "individual",
    model = "twosteps",
    transformation = "d",
    collapse = TRUE
  )
}, error = function(e) e)

if (inherits(diff_result, "error")) {
  run_log <- rbind(run_log, data.frame(
    model = "Difference GMM",
    status = "ERROR",
    message = diff_result$message
  ))
} else {
  diff_tidy <- tidy_pgmm(diff_result, "Difference GMM")
  write.csv(
    diff_tidy,
    file.path(outdir, "25_r_plm_difference_gmm_results.csv"),
    row.names = FALSE
  )
  run_log <- rbind(run_log, data.frame(
    model = "Difference GMM",
    status = "OK",
    message = "plm::pgmm difference GMM completed"
  ))
}

# System GMM
# In plm::pgmm, transformation = "ld" corresponds to system GMM.
sys_result <- tryCatch({
  pgmm(
    y ~ lag(y, 1) + x_pred + x_exog |
      lag(y, 2:3) + lag(x_pred, 2:3) + x_exog,
    data = pdata,
    effect = "individual",
    model = "twosteps",
    transformation = "ld",
    collapse = TRUE
  )
}, error = function(e) e)

if (inherits(sys_result, "error")) {
  run_log <- rbind(run_log, data.frame(
    model = "System GMM",
    status = "ERROR",
    message = sys_result$message
  ))
} else {
  sys_tidy <- tidy_pgmm(sys_result, "System GMM")
  write.csv(
    sys_tidy,
    file.path(outdir, "25_r_plm_system_gmm_results.csv"),
    row.names = FALSE
  )
  run_log <- rbind(run_log, data.frame(
    model = "System GMM",
    status = "OK",
    message = "plm::pgmm system GMM completed"
  ))
}

write.csv(
  run_log,
  file.path(outdir, "25_r_plm_run_log.csv"),
  row.names = FALSE
)

print(run_log)
