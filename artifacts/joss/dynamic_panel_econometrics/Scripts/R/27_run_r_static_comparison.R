# Artifact 27: R static/panel/IV comparison
# Outputs R results for OLS, pooled OLS, FE, RE, and 2SLS.

required <- c("plm", "AER")

for (pkg in required) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

library(plm)
library(AER)

root <- "C:/Users/omoko/OneDrive/Papers/Dynamic_Panel_Econometrics"
setwd(root)

outdir <- file.path(root, "Artifacts/Joss/tables/27_static_cross_software_comparison")
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

data_path <- file.path(root, "Data/Processed/22_dynamic_gmm_controlled_panel.csv")
df <- read.csv(data_path)

df <- df[order(df$id, df$time), ]

if (!("L1_y" %in% names(df))) {
  df$L1_y <- ave(df$y, df$id, FUN = function(x) c(NA, x[-length(x)]))
}

df$L2_x_pred <- ave(df$x_pred, df$id, FUN = function(x) c(NA, NA, x[-c(length(x)-1, length(x))]))

static <- na.omit(df[, c("id", "time", "y", "L1_y", "x_pred", "x_exog")])
ivdata <- na.omit(df[, c("id", "time", "y", "L1_y", "x_pred", "x_exog", "L2_x_pred")])

pdata <- pdata.frame(static, index = c("id", "time"))

tidy_lm <- function(model, model_name, package_name) {
  s <- summary(model)
  co <- as.data.frame(coef(s))
  co$term <- rownames(co)
  rownames(co) <- NULL

  names(co) <- make.names(names(co))

  estimate_col <- grep("Estimate", names(co), value = TRUE)[1]
  se_col <- grep("Std", names(co), value = TRUE)[1]
  stat_col <- grep("t.value|z.value", names(co), value = TRUE)[1]
  p_col <- grep("Pr", names(co), value = TRUE)[1]

  out <- data.frame(
    model = model_name,
    software = package_name,
    language = "R",
    term = co$term,
    coefficient = as.numeric(co[[estimate_col]]),
    std_error = as.numeric(co[[se_col]]),
    statistic = as.numeric(co[[stat_col]]),
    p_value = as.numeric(co[[p_col]]),
    stringsAsFactors = FALSE
  )

  out$term_norm <- out$term
  out$term_norm[out$term_norm == "(Intercept)"] <- "const"
  out
}

tidy_plm <- function(model, model_name) {
  tidy_lm(model, model_name, "R plm")
}

run_log <- data.frame(model=character(), status=character(), message=character(), stringsAsFactors=FALSE)

# OLS
tryCatch({
  m <- lm(y ~ L1_y + x_pred + x_exog, data = static)
  write.csv(tidy_lm(m, "OLS", "R lm"), file.path(outdir, "27_r_ols_results.csv"), row.names = FALSE)
  run_log <- rbind(run_log, data.frame(model="OLS", status="OK", message="R lm completed"))
}, error=function(e) {
  run_log <<- rbind(run_log, data.frame(model="OLS", status="ERROR", message=e$message))
})

# Pooled OLS
tryCatch({
  m <- plm(y ~ L1_y + x_pred + x_exog, data = pdata, model = "pooling")
  write.csv(tidy_plm(m, "Pooled OLS"), file.path(outdir, "27_r_pooled_ols_results.csv"), row.names = FALSE)
  run_log <- rbind(run_log, data.frame(model="Pooled OLS", status="OK", message="plm pooling completed"))
}, error=function(e) {
  run_log <<- rbind(run_log, data.frame(model="Pooled OLS", status="ERROR", message=e$message))
})

# Fixed Effects
tryCatch({
  m <- plm(y ~ L1_y + x_pred + x_exog, data = pdata, model = "within", effect = "individual")
  write.csv(tidy_plm(m, "Fixed Effects"), file.path(outdir, "27_r_fe_results.csv"), row.names = FALSE)
  run_log <- rbind(run_log, data.frame(model="Fixed Effects", status="OK", message="plm within individual completed"))
}, error=function(e) {
  run_log <<- rbind(run_log, data.frame(model="Fixed Effects", status="ERROR", message=e$message))
})

# Random Effects
tryCatch({
  m <- plm(y ~ L1_y + x_pred + x_exog, data = pdata, model = "random", effect = "individual")
  write.csv(tidy_plm(m, "Random Effects"), file.path(outdir, "27_r_re_results.csv"), row.names = FALSE)
  run_log <- rbind(run_log, data.frame(model="Random Effects", status="OK", message="plm random completed"))
}, error=function(e) {
  run_log <<- rbind(run_log, data.frame(model="Random Effects", status="ERROR", message=e$message))
})

# 2SLS
tryCatch({
  m <- ivreg(y ~ L1_y + x_exog + x_pred | L1_y + x_exog + L2_x_pred, data = ivdata)
  write.csv(tidy_lm(m, "2SLS", "R AER::ivreg"), file.path(outdir, "27_r_2sls_results.csv"), row.names = FALSE)
  run_log <- rbind(run_log, data.frame(model="2SLS", status="OK", message="AER::ivreg completed"))
}, error=function(e) {
  run_log <<- rbind(run_log, data.frame(model="2SLS", status="ERROR", message=e$message))
})

write.csv(run_log, file.path(outdir, "27_r_static_run_log.csv"), row.names = FALSE)
print(run_log)
