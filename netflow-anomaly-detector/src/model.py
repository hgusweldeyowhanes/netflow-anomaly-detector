"""
Anomaly scoring model.

Wraps scikit-learn's IsolationForest (or LocalOutlierFactor) with:
  - feature scaling
  - a 0-100 "risk score" transform (100 = most anomalous) instead of the raw,
    hard-to-interpret decision_function output
  - simple feature-attribution: for each flagged window, report which
    features deviated most from the population mean (in standard deviations),
    so an analyst gets a "why" and not just a number
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler


class AnomalyModel:
    def __init__(self, feature_columns, model_type="isolation_forest",
                 contamination=0.02, n_estimators=200, random_state=42):
        self.feature_columns = feature_columns
        self.model_type = model_type
        self.scaler = StandardScaler()

        if model_type == "isolation_forest":
            self.model = IsolationForest(
                n_estimators=n_estimators,
                contamination=contamination,
                random_state=random_state,
            )
        elif model_type == "lof":
            self.model = LocalOutlierFactor(
                n_neighbors=20, contamination=contamination, novelty=False
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    def fit_predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """Fit on the given feature set and return it annotated with risk scores."""
        X = features[self.feature_columns].values
        X_scaled = self.scaler.fit_transform(X)

        result = features.copy()

        if self.model_type == "isolation_forest":
            self.model.fit(X_scaled)
            raw_scores = self.model.decision_function(X_scaled)  # higher = more normal
            preds = self.model.predict(X_scaled)                  # -1 = anomaly, 1 = normal
        else:  # LOF, fit_predict only
            preds = self.model.fit_predict(X_scaled)
            raw_scores = self.model.negative_outlier_factor_

        # Convert raw_scores (higher = more normal) into a 0-100 risk score
        # (higher = more anomalous), scaled by min/max within this batch.
        min_s, max_s = raw_scores.min(), raw_scores.max()
        span = (max_s - min_s) or 1e-9
        risk_score = 100 * (1 - (raw_scores - min_s) / span)

        result["raw_score"] = raw_scores
        result["risk_score"] = np.round(risk_score, 1)
        result["is_anomaly"] = preds == -1

        # Per-row feature attribution: z-score of each feature vs. population
        z_scores = pd.DataFrame(X_scaled, columns=self.feature_columns, index=features.index)
        result["_zscores"] = z_scores.apply(lambda row: row.to_dict(), axis=1)

        return result

    @staticmethod
    def top_contributing_features(zscore_dict: dict, top_n: int = 5):
        """Return the top_n features with the largest absolute z-score deviation."""
        ranked = sorted(zscore_dict.items(), key=lambda kv: abs(kv[1]), reverse=True)
        return [
            {"feature": name, "zscore": round(float(val), 2), "direction": "high" if val > 0 else "low"}
            for name, val in ranked[:top_n]
        ]
