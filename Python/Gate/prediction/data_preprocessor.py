"""Data preprocessing module.

Responsible for feature engineering, normalization,
sliding window segmentation, and missing value processing.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Data preprocessor.

    Performs feature engineering, normalization, sliding window segmentation,
    and other preprocessing operations.

    Attributes:
        feature_columns: List of feature column names.
        normalization_method: Normalization method ('minmax' or 'standard').
        normalization_params: Normalization parameters.
    """

    def __init__(
        self,
        feature_columns: List[str],
        normalization_method: str = "minmax"
    ):
        """Initialize the data preprocessor.

        Args:
            feature_columns: List of feature column names.
            normalization_method: Normalization method, 'minmax' or 'standard'.
        """
        self.feature_columns = feature_columns
        self.normalization_method = normalization_method
        self.normalization_params: Dict[str, Dict] = {}

        logger.info(
            "Data preprocessor initialized, feature count: %d, normalization method: %s",
            len(feature_columns),
            normalization_method
        )

    def fit(self, df: pd.DataFrame) -> None:
        """Fit normalization parameters.

        Calculates normalization parameters based on training data and saves them.

        Args:
            df: DataFrame containing feature data.
        """
        if df.empty:
            logger.warning("DataFrame is empty, cannot fit normalization parameters")
            return

        for col in self.feature_columns:
            if col not in df.columns:
                logger.warning("Feature column '%s' does not exist in DataFrame", col)
                continue

            col_data = df[col].dropna()

            if self.normalization_method == "minmax":
                self.normalization_params[col] = {
                    "min": col_data.min(),
                    "max": col_data.max(),
                }
            elif self.normalization_method == "standard":
                self.normalization_params[col] = {
                    "mean": col_data.mean(),
                    "std": col_data.std() if col_data.std() > 0 else 1.0,
                }

        logger.info("Normalization parameter fitting complete, %d features", len(self.normalization_params))

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform data by applying normalization.

        Args:
            df: DataFrame containing feature data.

        Returns:
            Normalized feature matrix, shape=(n_samples, n_features).
        """
        if df.empty:
            logger.warning("DataFrame is empty, returning empty array")
            return np.array([])

        if not self.normalization_params:
            logger.warning("Normalization parameters not fitted, using raw data")
            return df[self.feature_columns].values

        features_list = []
        for col in self.feature_columns:
            if col not in df.columns:
                logger.warning("Feature column '%s' does not exist, filling with 0", col)
                features_list.append(np.zeros(len(df)))
                continue

            col_data = df[col].values.copy()

            # Handle missing values
            nan_mask = np.isnan(col_data)
            if nan_mask.any():
                # Use forward fill or mean fill
                if col in self.normalization_params:
                    if self.normalization_method == "minmax":
                        fill_value = self.normalization_params[col]["min"]
                    else:
                        fill_value = self.normalization_params[col]["mean"]
                    col_data[nan_mask] = fill_value
                else:
                    col_data[nan_mask] = 0.0

            # Apply normalization
            if col in self.normalization_params:
                params = self.normalization_params[col]
                if self.normalization_method == "minmax":
                    min_val = params["min"]
                    max_val = params["max"]
                    if max_val > min_val:
                        col_data = (col_data - min_val) / (max_val - min_val)
                    else:
                        col_data = np.zeros_like(col_data)
                elif self.normalization_method == "standard":
                    mean_val = params["mean"]
                    std_val = params["std"]
                    col_data = (col_data - mean_val) / std_val

            features_list.append(col_data)

        features = np.column_stack(features_list)
        return features

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fit and transform data.

        Args:
            df: DataFrame containing feature data.

        Returns:
            Normalized feature matrix.
        """
        self.fit(df)
        return self.transform(df)

    def create_sequences(
        self,
        features: np.ndarray,
        seq_length: int,
        step: int = 1
    ) -> np.ndarray:
        """Create sliding window sequences.

        Splits continuous time-series data into multiple sliding windows.

        Args:
            features: Feature matrix, shape=(n_samples, n_features).
            seq_length: Sequence length.
            step: Sliding step, default is 1.

        Returns:
            Sequence array, shape=(n_sequences, seq_length, n_features).
        """
        if len(features) < seq_length:
            logger.warning(
                "Insufficient feature data, need %d, have %d",
                seq_length,
                len(features)
            )
            return np.array([])

        sequences = []
        for i in range(0, len(features) - seq_length + 1, step):
            sequences.append(features[i:i + seq_length])

        sequences = np.array(sequences)
        logger.info(
            "Created %d sequences, shape=%s",
            len(sequences),
            sequences.shape
        )
        return sequences

    def prepare_model_input(
        self,
        df: pd.DataFrame,
        seq_length: int,
        fit: bool = False
    ) -> Tuple[np.ndarray, Dict]:
        """Prepare model input data.

        Complete data preprocessing pipeline: normalization + sliding window segmentation.

        Args:
            df: DataFrame containing sensor data.
            seq_length: Sequence length.
            fit: Whether to fit normalization parameters.

        Returns:
            (Sequence array, Preprocessing statistics)
        """
        stats = {
            "total_samples": len(df),
            "features_used": len(self.feature_columns),
            "sequences_created": 0,
            "normalization_applied": self.normalization_method,
        }

        if df.empty:
            logger.warning("DataFrame is empty, cannot prepare model input")
            return np.array([]), stats

        # Normalization
        if fit:
            features = self.fit_transform(df)
        else:
            features = self.transform(df)

        # Sliding window segmentation
        sequences = self.create_sequences(features, seq_length)
        stats["sequences_created"] = len(sequences)

        return sequences, stats

    def get_normalization_params(self) -> Dict[str, Dict]:
        """Get normalization parameters.

        Returns:
            Dictionary of normalization parameters.
        """
        return self.normalization_params.copy()

    def set_normalization_params(self, params: Dict[str, Dict]) -> None:
        """Set normalization parameters.

        Used for loading saved normalization parameters from external sources.

        Args:
            params: Dictionary of normalization parameters.
        """
        self.normalization_params = params.copy()
        logger.info("Loaded normalization parameters, %d features", len(params))

    def inverse_transform(
        self,
        normalized_data: np.ndarray,
        feature_index: int
    ) -> np.ndarray:
        """Inverse transform.

        Converts normalized data back to the original scale.

        Args:
            normalized_data: Normalized data.
            feature_index: Feature index.

        Returns:
            Data in the original scale.
        """
        if feature_index >= len(self.feature_columns):
            logger.warning("Feature index out of bounds: %d", feature_index)
            return normalized_data

        col = self.feature_columns[feature_index]
        if col not in self.normalization_params:
            logger.warning("Feature '%s' has no normalization parameters", col)
            return normalized_data

        params = self.normalization_params[col]
        if self.normalization_method == "minmax":
            min_val = params["min"]
            max_val = params["max"]
            return normalized_data * (max_val - min_val) + min_val
        elif self.normalization_method == "standard":
            mean_val = params["mean"]
            std_val = params["std"]
            return normalized_data * std_val + mean_val

        return normalized_data

    def save_params(self, filepath: str) -> bool:
        """Save normalization parameters to file.

        Args:
            filepath: File path.

        Returns:
            True if saved successfully, False if failed.
        """
        try:
            import json

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.normalization_params, f, indent=2)

            logger.info("Normalization parameters saved to: %s", filepath)
            return True

        except Exception as error:
            logger.error("Failed to save normalization parameters: %s", error)
            return False

    def load_params(self, filepath: str) -> bool:
        """Load normalization parameters from file.

        Args:
            filepath: File path.

        Returns:
            True if loaded successfully, False if failed.
        """
        try:
            import json

            with open(filepath, 'r', encoding='utf-8') as f:
                params = json.load(f)

            self.normalization_params = params
            logger.info("Loaded normalization parameters from %s, %d features", filepath, len(params))
            return True

        except Exception as error:
            logger.error("Failed to load normalization parameters: %s", error)
            return False
