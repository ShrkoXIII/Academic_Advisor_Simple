"""Isolated compatible B/C models, with earlier-semester research features.

The original production artifacts remain read-only. All derived history,
models and validation metrics live under the private pilot experiments tree.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from src import paths
from src.features.feature_contract import CATEGORICAL_FEATURES, learn_category_levels
from src.features.frozen_history import file_sha256
from src.grade_scale import GradeScale
from src.modeling.training_config import training_weights
from scripts.experiments.attempt_sum_removal.history import compute_plan_context
from scripts.experiments.attempt_sum_removal.contract import PLAN_COLUMNS
from .adapter import HISTORY_AS_OF_PART, PILOT_ROOT, TARGET_PART
from .enhanced import B_FEATURES, PEER_FIELDS
from .history import OUTPUT_COLUMNS, UniversityHistory


C_ADDITIONS = ["course_difficulty_gap", "peer_expected_points", "similar_peer_support"]
C_FEATURES = [*B_FEATURES, *C_ADDITIONS]
REFERENCE_COLUMNS = ["student_course_id", "student_id", "degree_id", "course_id", "part_id",
                     "grade_version_id", "points", "final_mark", "course_credits",
                     "start_agpa_points", "start_total_in_credits", "degree_credits_count",
                     "gpa_trend_delta", "prior_total_fail_courses"]
MODEL_PARAMETERS = {
    "learning_rate": .04, "num_leaves": 31, "min_data_in_leaf": 80,
    "feature_fraction": .9, "bagging_fraction": .9, "bagging_freq": 1,
    "lambda_l1": .1, "lambda_l2": 1., "max_bin": 255,
    "verbosity": -1, "seed": 42, "feature_fraction_seed": 42,
    "bagging_seed": 42, "data_random_seed": 42,
    "deterministic": True, "force_col_wise": True, "num_threads": 4,
}
PLAN_CONTEXT_PROTOCOL = "full_registration_roster_v1"
ROSTER_COLUMNS = ["student_course_id", "student_id", "degree_id", "course_id", "part_id", "course_credits"]


def model_matrix(frame, levels, features):
    """Use the explicit isolated schema, preserving absent numeric evidence."""
    if len(set(features)) != len(features) or not set(features).issubset(C_FEATURES):
        raise ValueError("Unsupported isolated model feature contract.")
    missing = set(features) - set(frame)
    if missing:
        raise ValueError("Missing isolated model inputs: " + ", ".join(sorted(missing)))
    result = pd.DataFrame(index=frame.index)
    for column in features:
        if column in CATEGORICAL_FEATURES:
            values = frame[column].astype("string").fillna("__MISSING__")
            result[column] = pd.Categorical(values.where(values.isin(levels[column]), "__UNKNOWN__"),
                                            categories=levels[column])
        else:
            result[column] = pd.to_numeric(frame[column], errors="coerce").astype("float32")
    return result


def temporal_split(frame, *, validation_part=20243):
    """The held-out historical semester never contributes fitted labels."""
    if validation_part >= TARGET_PART:
        raise ValueError("Validation must precede the pilot target semester.")
    parts = pd.to_numeric(frame.part_id, errors="raise")
    return frame.loc[parts.lt(validation_part)].copy(), frame.loc[parts.eq(validation_part)].copy()


def _peer_dimensions(frame):
    result = frame[[c for c in PEER_FIELDS if c != "academic_progress"]].apply(pd.to_numeric, errors="coerce")
    denominator = pd.to_numeric(frame.degree_credits_count, errors="coerce")
    result["academic_progress"] = pd.to_numeric(frame.start_total_in_credits, errors="coerce").div(
        denominator.where(denominator.gt(0)))
    return result[PEER_FIELDS].to_numpy(dtype=float, na_value=np.nan)


def research_features(frame, reference, *, k=20, min_support=5):
    """Compute actual prior marks and other-student points; no mark-to-points mean.

    KNN uses the existing five beginning-of-semester dimensions, at least
    three jointly observed dimensions and one latest prior record per peer.
    Rows from the same semester, future, or target student cannot be peers.
    """
    if k < 1 or min_support < 1:
        raise ValueError("Positive peer limits are required.")
    missing = set(REFERENCE_COLUMNS) - set(reference)
    required_queries = set(REFERENCE_COLUMNS) - {"student_course_id", "points", "final_mark"}
    if missing or not required_queries.issubset(frame):
        raise ValueError("Research feature source/query schema is incomplete.")
    query = frame.reset_index(drop=True).copy()
    source = reference.loc[pd.to_numeric(reference.part_id).lt(TARGET_PART)].copy()
    source["part_id"] = pd.to_numeric(source.part_id).astype(int)
    for column in ["student_id", "degree_id", "course_id", "grade_version_id"]:
        query[column] = query[column].astype("string")
        source[column] = source[column].astype("string")
    source = source.sort_values(["part_id", "student_course_id"], kind="stable").reset_index(drop=True)
    result = pd.DataFrame({"course_difficulty_gap": np.nan, "peer_expected_points": np.nan,
                           "similar_peer_support": 0, "peer_max_source_part": np.nan}, index=query.index)
    dimensions = _peer_dimensions(query)
    source_dimensions = _peer_dimensions(source)
    grouping = ["degree_id", "course_id", "grade_version_id"]
    source_groups = {key: group for key, group in source.groupby(grouping, sort=False, observed=True)}
    for part, part_rows in query.groupby("part_id", sort=False, observed=True):
        prefix = source.loc[source.part_id.lt(int(part))]
        marks = pd.to_numeric(prefix.final_mark, errors="coerce")
        credits = pd.to_numeric(prefix.course_credits, errors="coerce")
        usable = marks.between(0, 100) & credits.gt(0) & np.isfinite(credits)
        own = prefix.loc[usable].assign(_mark_credit=marks[usable] * credits[usable], _credits=credits[usable])
        own = own.groupby(["student_id", "degree_id"], observed=True)[["_mark_credit", "_credits"]].sum()
        own_means = own._mark_credit.div(own._credits)
        lookup = pd.MultiIndex.from_frame(part_rows[["student_id", "degree_id"]])
        own_reference = own_means.reindex(lookup).to_numpy(dtype=float)
        if "course_history_avg_mark" in query:
            averages = pd.to_numeric(part_rows.course_history_avg_mark, errors="coerce").to_numpy(dtype=float)
            result.loc[part_rows.index, "course_difficulty_gap"] = own_reference - averages
        for key, targets in part_rows.groupby(grouping, sort=False, observed=True):
            population = source_groups.get(key)
            if population is None:
                continue
            population = population.loc[population.part_id.lt(int(part))].drop_duplicates("student_id", keep="last")
            points = pd.to_numeric(population.points, errors="coerce")
            population = population.loc[points.between(0, 4)]
            if population.empty:
                continue
            values = source_dimensions[population.index.to_numpy()]
            source_ids = population.student_id.to_numpy(dtype=str)
            point_values = pd.to_numeric(population.points).to_numpy(dtype=float)
            source_parts = population.part_id.to_numpy(dtype=int)
            finite = np.isfinite(values)
            totals = np.where(finite, values, 0).sum(axis=0)
            squared = np.where(finite, values ** 2, 0).sum(axis=0)
            counts = finite.sum(axis=0)
            positions = targets.index.to_numpy()
            for start in range(0, len(positions), 128):
                indices = positions[start:start + 128]
                target_values = dimensions[indices]
                same_student = query.loc[indices, "student_id"].to_numpy(dtype=str)[:, None] == source_ids
                omitted = same_student.astype(float)
                remaining_counts = counts[None, :] - omitted @ finite.astype(float)
                remaining_totals = totals[None, :] - omitted @ np.where(finite, values, 0)
                remaining_squared = squared[None, :] - omitted @ np.where(finite, values ** 2, 0)
                denominator = np.maximum(remaining_counts, 1)
                variance = remaining_squared / denominator - (remaining_totals / denominator) ** 2
                scales = np.sqrt(np.maximum(variance, 0))
                scales[~np.isfinite(scales) | (scales == 0)] = 1.
                valid = finite[None, :, :] & np.isfinite(target_values)[:, None, :]
                differences = np.where(valid, (values[None, :, :] - target_values[:, None, :]) / scales[:, None, :], 0)
                shared = valid.sum(axis=2)
                distance = np.sqrt(np.square(differences).sum(axis=2) / np.maximum(shared, 1))
                distance[(shared < 3) | same_student] = np.inf
                nearest = np.argsort(distance, axis=1, kind="stable")[:, :k]
                for number, index in enumerate(indices):
                    selected = nearest[number][np.isfinite(distance[number, nearest[number]])]
                    result.at[index, "similar_peer_support"] = len(selected)
                    if len(selected):
                        result.at[index, "peer_max_source_part"] = source_parts[selected].max()
                    if len(selected) >= min_support:
                        result.at[index, "peer_expected_points"] = point_values[selected].mean()
    result.index = frame.index
    return result


def _prepare_rows(frame, history):
    rows = frame.copy()
    rows[list(OUTPUT_COLUMNS)] = history.apply(rows)
    groups = ["plan_id"] if "plan_id" in rows else ["student_id", "degree_id", "part_id"]
    context = compute_plan_context(rows, group_columns=groups)
    rows[context.columns] = context
    return rows


def prepare_training_rows(labels, roster, history):
    """Use the full registered plan, then retain only finalized labeled rows.

    Withdrawn/unfinalized registered courses contribute known plan properties
    and strictly prior UniversityHistory only. Their outcomes are never read.
    """
    for name, frame in [("labels", labels), ("roster", roster)]:
        if not set(ROSTER_COLUMNS).issubset(frame) or frame[ROSTER_COLUMNS].isna().any().any():
            raise ValueError(f"Training {name} requires complete registration keys and credits.")
        if frame.student_course_id.duplicated().any():
            raise ValueError(f"Training {name} has duplicate student_course_id.")
    rows = labels.loc[pd.to_numeric(labels.part_id).le(HISTORY_AS_OF_PART)].copy()
    registration = roster.loc[pd.to_numeric(roster.part_id).le(HISTORY_AS_OF_PART), ROSTER_COLUMNS].copy()
    keyed = registration.set_index("student_course_id")
    if not rows.student_course_id.isin(keyed.index).all():
        raise ValueError("Finalized labeled row is missing from the full registration roster.")
    matched = keyed.reindex(rows.student_course_id)
    for name in ["student_id", "degree_id", "course_id", "part_id", "course_credits"]:
        expected, observed = rows[name].reset_index(drop=True), matched[name].reset_index(drop=True)
        equal = (pd.to_numeric(expected).eq(pd.to_numeric(observed)) if name in ["part_id", "course_credits"]
                 else expected.astype("string").eq(observed.astype("string")))
        if not equal.all():
            raise ValueError("Finalized/roster identity mismatch: " + name)
    features = _prepare_rows(registration, history).set_index("student_course_id")
    columns = [*OUTPUT_COLUMNS, *PLAN_COLUMNS]
    recomputed = features.reindex(rows.student_course_id)[columns]
    changed_counts = (pd.to_numeric(rows.plan_course_count).ne(recomputed.plan_course_count.to_numpy()).sum()
                      if "plan_course_count" in rows else None)
    changed_credits = (pd.to_numeric(rows.plan_total_credits).ne(recomputed.plan_total_credits.to_numpy()).sum()
                       if "plan_total_credits" in rows else None)
    rows[columns] = recomputed.to_numpy()
    return rows, {"protocol": PLAN_CONTEXT_PROTOCOL, "roster_rows": len(registration),
                  "labeled_rows": len(rows), "roster_only_rows": int((~registration.student_course_id.isin(rows.student_course_id)).sum()),
                  "roster_outcomes_used": False, "join_key": "student_course_id",
                  "identity_fields_verified": ["student_id", "degree_id", "course_id", "part_id", "course_credits"],
                  "plan_course_count_rows_changed_from_source": int(changed_counts) if changed_counts is not None else None,
                  "plan_total_credits_rows_changed_from_source": int(changed_credits) if changed_credits is not None else None}


def serving_research_features(frame, reference, *, k=20, min_support=5):
    """Predict each distinct course context once, then restore all plan rows."""
    keys = ["student_id", "degree_id", "course_id", "part_id", "grade_version_id",
            "degree_credits_count", "course_history_avg_mark",
            *[name for name in PEER_FIELDS if name != "academic_progress"]]
    keys = list(dict.fromkeys(keys))
    codes, _ = pd.factorize(pd.MultiIndex.from_frame(frame[keys]), sort=False)
    selected = ~pd.Series(codes).duplicated().to_numpy()
    unique = frame.loc[selected].reset_index(drop=True)
    result = research_features(unique, reference, k=k, min_support=min_support)
    expanded = result.iloc[codes].copy()
    expanded.index = frame.index
    return expanded


def _fit_pair(fit, valid, features, *, rounds=250):
    import lightgbm as lgb
    levels = learn_category_levels(fit)
    fit_matrix = model_matrix(fit, levels, features)
    valid_matrix = model_matrix(valid, levels, features) if valid is not None else None
    fitted, metrics = {}, {}
    for task, target in [("grade", "final_mark"), ("fail", "is_fail")]:
        params = {**MODEL_PARAMETERS, "objective": "regression" if task == "grade" else "binary",
                  "metric": "mae" if task == "grade" else "binary_logloss"}
        dataset = lgb.Dataset(fit_matrix, label=pd.to_numeric(fit[target]),
                              weight=training_weights(fit), categorical_feature=CATEGORICAL_FEATURES)
        callbacks = [lgb.log_evaluation(0)]
        valid_sets = None
        if valid is not None:
            valid_sets = [lgb.Dataset(valid_matrix, label=pd.to_numeric(valid[target]), reference=dataset)]
            callbacks.append(lgb.early_stopping(30, first_metric_only=True, verbose=False))
        model = lgb.train(params, dataset, num_boost_round=rounds, valid_sets=valid_sets, callbacks=callbacks)
        fitted[task] = model
        if valid is not None:
            prediction = model.predict(valid_matrix, num_threads=4)
            actual = pd.to_numeric(valid[target]).to_numpy(dtype=float)
            if task == "grade":
                metrics.update(grade_mae=float(np.abs(actual - prediction).mean()),
                               grade_rmse=float(np.sqrt(np.square(actual - prediction).mean())))
            else:
                probability = np.clip(prediction, 1e-7, 1 - 1e-7)
                metrics.update(fail_brier=float(np.square(actual - probability).mean()),
                               fail_log_loss=float(-(actual * np.log(probability) + (1 - actual) * np.log(1 - probability)).mean()))
            metrics[f"{task}_iterations"] = model.best_iteration or model.current_iteration()
    return fitted, levels, metrics


def _write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def train_experiments(root=PILOT_ROOT, *, output_dir=None, source_path=None, roster_path=None, rounds=250):
    """Fit private B/C artifacts; validation labels are historical 20243 only."""
    from .history import build_experimental_university_history
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 1:
        raise ValueError("A positive integer boosting-round limit is required.")
    root = Path(root).resolve()
    model_root = root / "experiments" / "model_versions"
    output = Path(output_dir).resolve() if output_dir is not None else model_root / (
        datetime.now(timezone.utc).strftime("bc_%Y%m%dT%H%M%S_") + uuid4().hex[:8])
    if not output.is_relative_to(model_root):
        raise ValueError("Model output must be inside the isolated pilot model_versions directory.")
    protected = [paths.RAW_DIR, paths.CLEAN_DIR, paths.MERGED_DIR, paths.TEMPORAL_DIR,
                 paths.FEATURE_DIR, paths.ARTIFACT_DIR, paths.MODEL_DIR, PILOT_ROOT / "api_data"]
    if any(output.is_relative_to(directory.resolve()) for directory in protected):
        raise ValueError("Experimental training cannot write inside protected original data/model directories.")
    output.mkdir(parents=True, exist_ok=False)
    history_report = build_experimental_university_history(root, output / "history")
    if not history_report.get("usable_for_b_c"):
        raise ValueError("No audited experimental university history is available.")
    history_payload = json.loads((output / "history" / "university_history_experimental.json").read_text(encoding="utf-8"))
    history = UniversityHistory(history_payload["rows"], allow_incomplete_outcomes=True)
    source_path = Path(source_path or paths.TEMPORAL_TRAIN_FEATURES_PATH_V2)
    roster_path = Path(roster_path or paths.TEMPORAL_TRAIN_ROSTER_PATH_V2)
    source_hash = file_sha256(source_path)
    roster_hash = file_sha256(roster_path)
    columns = list(dict.fromkeys([*B_FEATURES, *REFERENCE_COLUMNS, "is_fail"]))
    raw = pd.read_parquet(source_path, columns=columns)
    parts = pd.to_numeric(raw.part_id, errors="raise")
    raw = raw.loc[parts.le(HISTORY_AS_OF_PART)].copy().reset_index(drop=True)
    if raw.empty or raw.student_course_id.duplicated().any():
        raise ValueError("Training needs unique finalized historical course rows.")
    marks = pd.to_numeric(raw.final_mark, errors="coerce")
    failures = pd.to_numeric(raw.is_fail, errors="coerce")
    if not marks.between(0, 100).all() or not failures.isin([0, 1]).all():
        raise ValueError("Historical targets are invalid.")
    roster = pd.read_parquet(roster_path, columns=ROSTER_COLUMNS)
    rows, roster_report = prepare_training_rows(raw, roster, history)
    _write_json(output / "training_roster_context.json", roster_report)
    research = research_features(rows, raw)
    rows[C_ADDITIONS] = research[C_ADDITIONS]
    fit, validation = temporal_split(rows)
    if fit.empty or validation.empty:
        raise ValueError("Historical temporal fit and validation rows are required.")
    variants = {"B": B_FEATURES, **{f"B_plus_{name}": [*B_FEATURES, name] for name in C_ADDITIONS}, "C": C_FEATURES}
    assessments = {}
    for name, features in variants.items():
        _, _, metrics = _fit_pair(fit, validation, features, rounds=rounds)
        assessments[name] = {"features": features, "feature_count": len(features), **metrics}
        _write_json(output / f"validation_{name}.json", assessments[name])
    final_models = {}
    for name, features in [("B", B_FEATURES), ("C", C_FEATURES)]:
        # Fixed validation-selected stopping count, then refit all finalized
        # historical rows through 20243. No 20251 outcome file is read.
        iterations = max(assessments[name]["grade_iterations"], assessments[name]["fail_iterations"])
        models, levels, _ = _fit_pair(rows, None, features, rounds=iterations)
        directory = output / name
        directory.mkdir()
        for task, model in models.items():
            model.save_model(str(directory / f"{task}_model.txt"))
        _write_json(directory / "category_levels.json", levels)
        artifact_hashes = {p.name: file_sha256(p) for p in directory.iterdir()}
        final_models[name] = {"features": features, "feature_count": len(features),
                              "training_as_of_part": HISTORY_AS_OF_PART,
                              "training_rows": len(rows), "iterations": iterations,
                              "artifact_sha256": artifact_hashes,
                              "validation": assessments[name]}
    reference_path = output / "individual_reference.parquet"
    raw[REFERENCE_COLUMNS].to_parquet(reference_path, index=False)
    manifest = {
        "format_version": 2, "status": "EXPERIMENTAL", "training_as_of_part": HISTORY_AS_OF_PART,
        "prediction_target_part": TARGET_PART, "selected_20251_outcomes_used": False,
        "production_activation": False, "seed": 42, "parameters": MODEL_PARAMETERS,
        "source_path": str(source_path.resolve()), "source_sha256": source_hash,
        "plan_context_protocol": PLAN_CONTEXT_PROTOCOL,
        "roster_source_path": str(roster_path.resolve()), "roster_source_sha256": roster_hash,
        "roster_context": roster_report, "grade_scale_sha256": file_sha256(paths.GRADE_SCALE_PATH),
        "training_rows": len(rows), "source_min_part": int(raw.part_id.min()),
        "source_max_part": int(raw.part_id.max()), "validation_part": 20243,
        "validation_fit_rows": len(fit), "validation_rows": len(validation),
        "validation_fit_max_part": int(fit.part_id.max()), "validation_assessments": assessments,
        "feature_coverage": {name: {"nonmissing_rows": int(rows[name].notna().sum()),
                                      "nonmissing_fraction": float(rows[name].notna().mean())} for name in C_ADDITIONS},
        "peer_source_max_part": int(research.peer_max_source_part.max()),
        "history": history_report, "experiments": final_models,
        "reference_sha256": file_sha256(reference_path),
        "history_sha256": file_sha256(output / "history" / "university_history_experimental.json"),
        "feature_method": {
            "peer_expected_points": "uniform k=20 distinct latest prior other-student KNN; minimum support 5; shared dimensions >=3",
            "similar_peer_support": "number of eligible neighbors among closest 20",
            "course_difficulty_gap": "own strictly-prior credit-weighted finalized marks minus UniversityHistory smoothed average marks; repeats retained as observed attempts",
            "student_relative_course_strength": "UNAVAILABLE: no trusted academic-domain taxonomy",
            "plan_difficulty_balance": "post-prediction diagnostic only; never a label or fitted feature",
        },
        "limitations": ["One held-out historical semester is not a 20251 accuracy estimate or recommendation-quality assessment.",
                        "C additions are measured individually; inclusion establishes supported inputs, not guaranteed improvement.",
                        "University-history source population differs from the cleaned finalized model-target population.",
                        "Missing student mark history or weak peer support remains missing, never filled with a synthetic outcome."]}
    if file_sha256(source_path) != source_hash:
        raise ValueError("Original individual source changed during training.")
    if file_sha256(roster_path) != roster_hash:
        raise ValueError("Original registration roster changed during training.")
    _write_json(output / "manifest.json", manifest)
    model_root.mkdir(parents=True, exist_ok=True)
    pointer = {"bundle": output.name, "status": "READY", "manifest_sha256": file_sha256(output / "manifest.json")}
    (model_root / "latest.json").write_text(json.dumps(pointer, indent=2), encoding="utf-8")
    return {"path": str(output), **manifest}


def load_model_bundle(path=None, *, root=PILOT_ROOT):
    """Verify schema, cutoffs and every private artifact before using a model."""
    import lightgbm as lgb
    if path is None:
        model_root = Path(root) / "experiments" / "model_versions"
        pointer = json.loads((model_root / "latest.json").read_text(encoding="utf-8"))
        if pointer.get("status") == "RETRACTED":
            raise ValueError("Private experimental model bundle has been retracted.")
        name = pointer["bundle"]
        if Path(name).name != name:
            raise ValueError("Invalid isolated model bundle path.")
        path = model_root / name
        if file_sha256(path / "manifest.json") != pointer["manifest_sha256"]:
            raise ValueError("Isolated model manifest fingerprint mismatch.")
    path = Path(path)
    retirement_path = path.parent / "retired_bundles.json"
    if retirement_path.exists() and path.name in json.loads(retirement_path.read_text(encoding="utf-8")):
        raise ValueError("Private experimental model bundle has been retired.")
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("training_as_of_part") != HISTORY_AS_OF_PART:
        raise ValueError("Invalid isolated training cutoff.")
    for name, features in [("B", B_FEATURES), ("C", C_FEATURES)]:
        if manifest.get("experiments", {}).get(name, {}).get("features") != features:
            raise ValueError("Incompatible isolated model feature contract.")
    if manifest.get("plan_context_protocol") != PLAN_CONTEXT_PROTOCOL:
        raise ValueError("Incompatible full-roster training context contract.")
    if file_sha256(paths.GRADE_SCALE_PATH) != manifest.get("grade_scale_sha256"):
        raise ValueError("GradeScale differs from the recorded training/serving artifact.")
    models, model_errors = {}, {}
    for name in "BC":
        directory = path / name
        try:
            for filename, expected in manifest["experiments"][name]["artifact_sha256"].items():
                if file_sha256(directory / filename) != expected:
                    raise ValueError("Isolated model artifact fingerprint mismatch.")
            levels = json.loads((directory / "category_levels.json").read_text(encoding="utf-8"))
            models[name] = {task: lgb.Booster(model_file=str(directory / f"{task}_model.txt")) for task in ["grade", "fail"]}
            models[name]["levels"] = levels
            if any(models[name][task].feature_name() != manifest["experiments"][name]["features"] for task in ["grade", "fail"]):
                raise ValueError("Saved model differs from isolated feature contract.")
        except (ValueError, OSError, KeyError, TypeError, lgb.basic.LightGBMError):
            models.pop(name, None)
            model_errors[name] = "MODEL_ARTIFACT_UNAVAILABLE_OR_INCOMPATIBLE"
    history_path = path / "history" / "university_history_experimental.json"
    reference_path = path / "individual_reference.parquet"
    if file_sha256(history_path) != manifest["history_sha256"] or file_sha256(reference_path) != manifest["reference_sha256"]:
        raise ValueError("Isolated research source fingerprint mismatch.")
    rows = json.loads(history_path.read_text(encoding="utf-8"))["rows"]
    return {"path": str(path), "manifest": manifest, "manifest_sha256": file_sha256(path / "manifest.json"),
            "models": models, "model_errors": model_errors,
            "history": UniversityHistory(rows, allow_incomplete_outcomes=True),
            "reference": pd.read_parquet(reference_path),
            "grade_scale": GradeScale.from_parquet(paths.GRADE_SCALE_PATH)}


def predict_course_rows(frame, experiment, *, num_threads=4, root=PILOT_ROOT, bundle=None):
    """Recompute the serving feature contract before genuine B/C prediction."""
    if experiment not in "BC" or len(experiment) != 1:
        raise ValueError("Only isolated experiments B and C are supported.")
    bundle = load_model_bundle(root=root) if bundle is None else bundle
    if experiment in bundle.get("model_errors", {}):
        raise ValueError(bundle["model_errors"][experiment])
    if not pd.to_numeric(frame.part_id).eq(TARGET_PART).all():
        raise ValueError("Pilot serving requires target semester 20251.")
    rows = _prepare_rows(frame, bundle["history"])
    if experiment == "C":
        features = serving_research_features(rows, bundle["reference"])
        rows[C_ADDITIONS] = features[C_ADDITIONS]
    contract = bundle["manifest"]["experiments"][experiment]["features"]
    models = bundle["models"][experiment]
    matrix = model_matrix(rows, models["levels"], contract)
    marks = np.asarray(models["grade"].predict(matrix, num_threads=num_threads), dtype=float)
    failures = np.asarray(models["fail"].predict(matrix, num_threads=num_threads), dtype=float)
    if marks.shape != (len(rows),) or failures.shape != (len(rows),) or not np.isfinite([marks, failures]).all():
        raise ValueError("Invalid isolated model predictions.")
    rows["predicted_mark"] = np.clip(marks, 0, 100)
    rows["fail_probability"] = np.clip(failures, 0, 1)
    rows["expected_points"], rows["expected_grade"] = bundle["grade_scale"].convert(rows.predicted_mark, rows.grade_version_id)
    return rows


class ExperimentalModels:
    """Lazy, cached access for a whole dashboard comparison batch."""

    def __init__(self, root=PILOT_ROOT, *, bundle_path=None):
        self.root, self.bundle_path, self._bundle = Path(root), bundle_path, None

    def _load(self):
        if self._bundle is None:
            self._bundle = load_model_bundle(self.bundle_path, root=self.root)
        return self._bundle

    def inspect(self):
        from lightgbm.basic import LightGBMError
        try:
            bundle = self._load()
            manifest = bundle["manifest"]
            history = manifest["history"]
            history_provenance = {
                "source_manifest_sha256": history.get("source_manifest_sha256"),
                "usable_rows_sha256": history.get("usable_rows_sha256"),
                "source_hashes": history.get("source_hashes", {}),
                "history_file_sha256": manifest["history_sha256"],
                "policy": history.get("history_policy_version"),
                "retainedstats": {key: history.get(key) for key in ["source_row_count", "validated_row_count",
                                                                     "quarantined_row_count", "retained_row_fraction"]},
                "audit": history,
            }
            result = {}
            for name in "BC":
                result[name] = {"status": "READY", **manifest["experiments"][name],
                    "model_version": Path(bundle["path"]).name, "bundle_path": bundle["path"],
                    "manifest_sha256": bundle["manifest_sha256"],
                    "history_as_of_part": HISTORY_AS_OF_PART, "history_provenance": history_provenance,
                    "reference_sha256": manifest["reference_sha256"],
                    "individual_source_sha256": manifest.get("source_sha256"),
                    "roster_source_sha256": manifest["roster_source_sha256"],
                    "roster_context": manifest.get("roster_context"),
                    "grade_scale_sha256": manifest["grade_scale_sha256"],
                    "historical_validation": {"validation_part": manifest.get("validation_part"),
                        "validation_fit_max_part": manifest.get("validation_fit_max_part"),
                        "validation_fit_rows": manifest.get("validation_fit_rows"),
                        "validation_rows": manifest.get("validation_rows"),
                        "assessments": manifest.get("validation_assessments", {})},
                    "usage": "isolated_experimental_prediction_only"}
                if name in bundle.get("model_errors", {}):
                    result[name].update(status="BLOCKED", reason=bundle["model_errors"][name])
            return result
        except (ValueError, OSError, KeyError, TypeError, LightGBMError):
            return {name: {"status": "BLOCKED", "reason": "COMPATIBLE_EXPERIMENTAL_MODEL_UNAVAILABLE"} for name in "BC"}

    def predict_course_rows(self, frame, experiment, *, num_threads=4):
        return predict_course_rows(frame, experiment, num_threads=num_threads, root=self.root, bundle=self._load())


def main(argv=None):
    """Explicit inspect/train commands; importing this module never trains."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--inspect", action="store_true")
    action.add_argument("--train", action="store_true")
    parser.add_argument("--root", type=Path, default=PILOT_ROOT)
    parser.add_argument("--rounds", type=int, default=250)
    args = parser.parse_args(argv)
    if args.inspect:
        result = ExperimentalModels(args.root).inspect()
    else:
        report = train_experiments(args.root, rounds=args.rounds)
        result = {key: report[key] for key in ["path", "training_rows", "training_as_of_part", "validation_assessments"]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
