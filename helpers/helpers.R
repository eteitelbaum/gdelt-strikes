# Helper: Compute deviance-based pseudo-R2 for GLMs
compute_pseudo_r2 <- function(y_true, y_pred, family = "poisson") {
  # Null model: predict mean
  y_mean <- mean(y_true)
  
  if (family == "poisson") {
    # Deviance for Poisson: 2 * sum(y * log(y/mu) - (y - mu))
    # Handle y=0 case where log(0) is undefined
    null_dev <- 2 * sum(y_true * ifelse(y_true > 0, log(y_true / y_mean), 0) - (y_true - y_mean))
    resid_dev <- 2 * sum(y_true * ifelse(y_true > 0, log(y_true / pmax(y_pred, 1e-10)), 0) - (y_true - pmax(y_pred, 1e-10)))
  } else if (family == "tweedie") {
    # Approximate with Poisson for now (proper Tweedie deviance requires the power parameter)
    null_dev <- 2 * sum(y_true * ifelse(y_true > 0, log(y_true / y_mean), 0) - (y_true - y_mean))
    resid_dev <- 2 * sum(y_true * ifelse(y_true > 0, log(y_true / pmax(y_pred, 1e-10)), 0) - (y_true - pmax(y_pred, 1e-10)))
  } else if (family == "gamma") {
    # Deviance for Gamma: 2 * sum(-log(y/mu) + (y - mu)/mu)
    # Only defined for y > 0
    y_pos <- y_true > 0
    null_dev <- 2 * sum(-log(y_true[y_pos] / y_mean) + (y_true[y_pos] - y_mean) / y_mean)
    resid_dev <- 2 * sum(-log(y_true[y_pos] / pmax(y_pred[y_pos], 1e-10)) + (y_true[y_pos] - pmax(y_pred[y_pos], 1e-10)) / pmax(y_pred[y_pos], 1e-10))
  }
  
  pseudo_r2 <- 1 - (resid_dev / null_dev)
  return(pseudo_r2)
}

# Helper: Duan's smearing estimate for log-scale models
compute_smearing_factor <- function(log_residuals) {
  mean(exp(log_residuals))
}

# Helper: Apply smearing correction to back-transform predictions
smearing_backtransform <- function(log_pred, smearing_factor) {
  smearing_factor * exp(log_pred)
}

# Helper: prediction wrapper for log-scale models (for permutation importance)
pred_wrapper_log <- function(object, newdata) {
  pmax(expm1(predict(object, new_data = newdata)$.pred), 0)
}

# Helper: collect per-fold predictions from tuning for the best configuration
collect_best_config_predictions <- function(tuned_res, model_name, model_type) {
  best_cfg <- select_best(tuned_res, metric = selection_metric)$.config
  preds <- tuned_res |>
    collect_predictions(summarize = FALSE) |>
    dplyr::filter(.config == best_cfg) |>
    dplyr::select(id, .pred, strike_count) |>
    dplyr::rename(truth = strike_count) |>
    dplyr::mutate(
      model = model_name,
      model_type = model_type,
      .pred_raw = dplyr::if_else(model_type == "log", .pred, NA_real_),
      .pred = dplyr::if_else(model_type == "log", pmax(expm1(.pred), 0), .pred)
    )
  preds
}

# Helper: compute per-fold metrics (standard + supplementary) from predictions
compute_metrics_from_preds <- function(preds_df, model_type) {
  # Pooled metrics across all folds (concatenated predictions)
  overall <- tibble::tibble(
    mae = yardstick::mae_vec(preds_df$truth, preds_df$.pred),
    rmse = yardstick::rmse_vec(preds_df$truth, preds_df$.pred),
    rsq = yardstick::rsq_vec(preds_df$truth, preds_df$.pred)
  )
  if (identical(model_type, "log") && ".pred_raw" %in% names(preds_df)) {
    overall$r2_log_scale <- yardstick::rsq_vec(log1p(preds_df$truth), preds_df$.pred_raw)
  }
  if (model_type %in% c("poisson", "tweedie")) {
    overall$pseudo_r2 <- compute_pseudo_r2(preds_df$truth, preds_df$.pred, family = model_type)
  }
  overall
}

# Helper: compute and save permutation importance per validation fold
compute_and_save_importance <- function(wf, splits, split_ids, model_name, model_type = "standard", nsim = 5) {
  dir.create("model_outputs/val_importance", recursive = TRUE, showWarnings = FALSE)
  results <- purrr::map2_dfr(splits, split_ids, function(split, id) {
    analysis_all <- analysis(split)
    fit_obj <- fit(wf, data = analysis_all)
    assess_all <- assessment(split)
    train_df <- dplyr::select(assess_all, -date)
    pred_fun <- NULL
    if (model_type == "log") pred_fun <- function(object, newdata) pred_wrapper_log(object, newdata)
    vi <- vip::vi_permute(
      fit_obj,
      train = train_df,
      target = "strike_count",
      metric = yardstick::rmse_vec,
      smaller_is_better = TRUE,
      nsim = nsim,
      pred_wrapper = pred_fun
    )
    tibble::tibble(
      model = model_name,
      fold_id = id,
      variable = vi$Variable,
      importance = vi$Importance
    )
  })
  arrow::write_parquet(results, sprintf("model_outputs/val_importance/%s_val_importance.parquet", model_name))
  invisible(results)
}

# Helper: evaluate on validation folds (supports optional backtransform and smearing)
# Returns metrics, predictions, and supplementary info for later analysis
collect_fold_metrics <- function(wf, splits, backtransform = identity, 
                                 model_type = "standard", use_smearing = FALSE,
                                 split_ids = NULL, model_name = NULL, 
                                 capture_last_fit = FALSE) {
  all_preds <- list()
  smear_factors <- list()
  
  last_fit_obj <- NULL  # Capture the last fitted model
  
  metrics <- purrr::map2_dfr(splits, if (is.null(split_ids)) rep(NA_character_, length(splits)) else split_ids, function(split, sid) {
    analysis_all <- analysis(split)
    assess_all <- assessment(split)
    fit_obj <- fit(wf, data = analysis_all)
    
    # Capture the last fitted model (which uses full pretest data in expanding window)
    if (capture_last_fit && sid == split_ids[length(split_ids)]) {
      last_fit_obj <<- fit_obj
    }
    
    preds_raw <- predict(fit_obj, new_data = assess_all)$.pred
    
    # Handle back-transformation with optional smearing
    if (use_smearing && model_type == "log") {
      # Calculate smearing factor from training residuals
      train_preds_log <- predict(fit_obj, new_data = analysis_all)$.pred
      log_resids <- log1p(analysis_all$strike_count) - train_preds_log
      smear_factor <- compute_smearing_factor(log_resids)
      preds <- smearing_backtransform(preds_raw, smear_factor)
      preds <- pmax(preds - 1, 0)  # Adjust for log1p offset
      smear_factors <<- c(smear_factors, list(tibble::tibble(
        model = if (is.null(model_name)) NA_character_ else model_name,
        fold_id = as.character(sid),
        smearing_factor = smear_factor
      )))
    } else {
      preds <- backtransform(preds_raw)
    }
    
    preds <- pmax(preds, 0)
    
    # Save predictions with raw (for log-scale metrics) and model type
    pred_df <- tibble(
      truth = assess_all$strike_count, 
      .pred = preds,
      model_type = model_type
    )
    # Save raw predictions for log models (needed for log-scale R²)
    if (model_type == "log") {
      pred_df$.pred_raw <- preds_raw
    }
    all_preds <<- c(all_preds, list(pred_df))
    
    # Standard metrics on original scale
    result <- tibble(
      mae = mae_vec(assess_all$strike_count, preds),
      rmse = rmse_vec(assess_all$strike_count, preds),
      rsq = rsq_vec(assess_all$strike_count, preds)
    )
    
    # Add pseudo-R2 for GLMs
    if (model_type %in% c("poisson", "tweedie")) {
      result$pseudo_r2 <- compute_pseudo_r2(assess_all$strike_count, preds, family = model_type)
    }
    
    # For log models, also report log-scale R2 for reference
    if (model_type == "log") {
      result$r2_log_scale <- rsq_vec(log1p(assess_all$strike_count), preds_raw)
    }
    
    result
  })
  
  preds_all <- dplyr::bind_rows(all_preds)
  # Compute pooled metrics across all folds (concatenated predictions)
  pooled <- tibble::tibble(
    mae = yardstick::mae_vec(preds_all$truth, preds_all$.pred),
    rmse = yardstick::rmse_vec(preds_all$truth, preds_all$.pred),
    rsq = yardstick::rsq_vec(preds_all$truth, preds_all$.pred)
  )
  if (identical(model_type, "log") && ".pred_raw" %in% names(preds_all)) {
    pooled$r2_log_scale <- yardstick::rsq_vec(log1p(preds_all$truth), preds_all$.pred_raw)
  }
  if (model_type %in% c("poisson", "tweedie")) {
    pooled$pseudo_r2 <- compute_pseudo_r2(preds_all$truth, preds_all$.pred, family = model_type)
  }
  
  # Return pooled one-row metrics, predictions, model type, smearing factors, and optionally last fitted model
  result_list <- list(
    metrics = pooled, 
    predictions = preds_all, 
    model_type = model_type,
    smear_factors = if (length(smear_factors) > 0) dplyr::bind_rows(smear_factors) else NULL
  )
  
  if (capture_last_fit) {
    result_list$last_fit <- last_fit_obj
  }
  
  result_list
}

# Helper to pull per-fold metrics for the selected .config
pull_best_fold_metrics <- function(tuned_res, model_type = "standard") {
  best_cfg <- select_best(tuned_res, metric = selection_metric)$.config

  # Return one row per fold (id) from tuning results for the selected config
  per_fold_metrics <- tuned_res |>
    collect_metrics(summarize = FALSE) |>
    dplyr::filter(.config == best_cfg) |>
    dplyr::group_by(id, .metric) |>
    dplyr::summarise(value = mean(.estimate, na.rm = TRUE), .groups = "drop_last") |>
    tidyr::pivot_wider(names_from = .metric, values_from = value) |>
    dplyr::mutate(
      mae = as.numeric(mae),
      rmse = as.numeric(rmse),
      rsq = as.numeric(rsq)
    ) |>
    dplyr::select(-id, mae, rmse, rsq)

  # Placeholders for metrics that require refitting/predictions
  if (model_type %in% c("poisson", "tweedie")) {
    per_fold_metrics$pseudo_r2 <- NA_real_
  }
  if (identical(model_type, "log")) {
    per_fold_metrics$r2_log_scale <- NA_real_
  }

  per_fold_metrics
}

# Helper: evaluate classifier on validation folds
# Returns OOF predictions (with probabilities), last fit, and pooled occurrence metrics
collect_occurrence_fold_metrics <- function(wf, splits, split_ids = NULL, 
                                           model_name = NULL, capture_last_fit = FALSE) {
  all_preds <- list()
  last_fit_obj <- NULL
  
  purrr::map2(splits, if (is.null(split_ids)) rep(NA_character_, length(splits)) else split_ids, 
              function(split, sid) {
    analysis_all <- rsample::analysis(split)
    assess_all <- rsample::assessment(split)
    fit_obj <- fit(wf, data = analysis_all)
    
    # Capture the last fitted model
    if (capture_last_fit && sid == split_ids[length(split_ids)]) {
      last_fit_obj <<- fit_obj
    }
    
    # Get probability predictions (both columns for yardstick compatibility)
    prob_obj <- predict(fit_obj, new_data = assess_all, type = "prob")
    
    # Save predictions
    pred_df <- tibble::tibble(
      truth = assess_all$y_occ,
      .pred_no = prob_obj$.pred_no,
      .pred_yes = prob_obj$.pred_yes,
      .row = seq_len(nrow(assess_all))
    )
    all_preds <<- c(all_preds, list(pred_df))
    
    NULL  # Don't return anything from map
  })
  
  # Combine all OOF predictions and explicitly ensure factor levels
  preds_all <- dplyr::bind_rows(all_preds) |>
    dplyr::mutate(truth = factor(truth, levels = c("no", "yes")))
  
  # Compute pooled occurrence metrics (uncalibrated probabilities)
  pooled <- tibble::tibble(
    pr_auc = yardstick::pr_auc_vec(preds_all$truth, preds_all$.pred_yes, event_level = "second"),
    roc_auc = yardstick::roc_auc_vec(preds_all$truth, preds_all$.pred_yes, event_level = "second"),
    brier = mean((preds_all$.pred_yes - as.numeric(preds_all$truth == "yes"))^2)  # Manual Brier calculation
  )
  
  # Return structure
  result_list <- list(
    metrics = pooled,
    predictions = preds_all
  )
  
  if (capture_last_fit) {
    result_list$last_fit <- last_fit_obj
  }
  
  result_list
}