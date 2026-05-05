"""Historical data collector module.

Responsible for pulling sensor historical data from MySQL database,
supporting time range queries and in-memory caching.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataCollector:
    """Historical data collector.

    Pulls sensor time-series data from MySQL database,
    supporting data caching and incremental updates.

    Attributes:
        db_conn: MySQL database connection object.
        cache_hours: Cache the last N hours of data.
        cache_df: Cached DataFrame.
        last_pull_time: Timestamp of the last data pull.
    """

    def __init__(self, db_conn, cache_hours: int = 168):
        """Initialize the data collector.

        Args:
            db_conn: MySQL database connection object.
            cache_hours: Cache the last N hours of data, default 168 hours (7 days).
        """
        self.db_conn = db_conn
        self.cache_hours = cache_hours
        self.cache_df: Optional[pd.DataFrame] = None
        self.last_pull_time: Optional[datetime] = None

        logger.info("Data collector initialized, cache window: %d hours", cache_hours)

    def pull_recent_data(self, hours: int = 24) -> pd.DataFrame:
        """Pull sensor data from the last N hours.

        Args:
            hours: Time range (hours), default 24 hours.

        Returns:
            DataFrame containing fields such as timestamp, temperature, humidity, etc.
            Returns an empty DataFrame if the query fails or no data is available.
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)

            sql = """
                SELECT 
                    timestamp,
                    light_th,
                    temperature,
                    humidity,
                    light_cu,
                    brightness,
                    curtain_status
                FROM gate_local_data
                WHERE timestamp >= %s AND timestamp <= %s
                ORDER BY timestamp ASC
            """

            df = pd.read_sql(
                sql,
                self.db_conn,
                params=(start_time.strftime("%Y-%m-%d %H:%M:%S"), 
                       end_time.strftime("%Y-%m-%d %H:%M:%S"))
            )

            if df.empty:
                logger.warning("Database query result is empty, time range: %s ~ %s", start_time, end_time)
            else:
                logger.info("Successfully pulled %d records, time range: %s ~ %s", 
                           len(df), df['timestamp'].min(), df['timestamp'].max())

            return df

        except Exception as error:
            logger.error("Failed to pull historical data: %s", error)
            return pd.DataFrame()

    def update_cache(self, incremental: bool = True) -> bool:
        """Update the in-memory cache.

        Args:
            incremental: Whether to perform incremental update.
                         True means only pull new data, False means full refresh.

        Returns:
            True if update succeeded, False if failed.
        """
        try:
            if incremental and self.cache_df is not None and self.last_pull_time is not None:
                # Incremental update: only pull new data since last update
                new_df = self.pull_data_since(self.last_pull_time)
                if not new_df.empty:
                    self.cache_df = pd.concat([self.cache_df, new_df], ignore_index=True)
                    # Remove expired data
                    cutoff_time = datetime.now() - timedelta(hours=self.cache_hours)
                    self.cache_df = self.cache_df[
                        self.cache_df['timestamp'] >= cutoff_time
                    ].reset_index(drop=True)
            else:
                # Full refresh
                self.cache_df = self.pull_recent_data(hours=self.cache_hours)

            self.last_pull_time = datetime.now()
            logger.info("Cache update successful, current cache contains %d records", len(self.cache_df) if self.cache_df is not None else 0)
            return True

        except Exception as error:
            logger.error("Failed to update cache: %s", error)
            return False

    def pull_data_since(self, since_time: datetime) -> pd.DataFrame:
        """Pull data after the specified timestamp.

        Args:
            since_time: The starting timestamp.

        Returns:
            DataFrame containing data after the specified time.
        """
        try:
            end_time = datetime.now()

            sql = """
                SELECT 
                    timestamp,
                    light_th,
                    temperature,
                    humidity,
                    light_cu,
                    brightness,
                    curtain_status
                FROM gate_local_data
                WHERE timestamp > %s AND timestamp <= %s
                ORDER BY timestamp ASC
            """

            df = pd.read_sql(
                sql,
                self.db_conn,
                params=(since_time.strftime("%Y-%m-%d %H:%M:%S"),
                       end_time.strftime("%Y-%m-%d %H:%M:%S"))
            )

            if not df.empty:
                logger.info("Incremental pull: %d new records", len(df))

            return df

        except Exception as error:
            logger.error("Failed to pull incremental data: %s", error)
            return pd.DataFrame()

    def get_cached_data(self) -> Optional[pd.DataFrame]:
        """Get a copy of the cached data.

        Returns:
            A copy of the cached DataFrame, or None if no cache exists.
        """
        if self.cache_df is not None:
            return self.cache_df.copy()
        return None

    def get_cache_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dictionary containing cache statistics:
            - total_samples: Total number of samples
            - time_range: Time range
            - memory_mb: Memory usage (MB)
            - last_pull_time: Last pull timestamp
        """
        stats = {
            "total_samples": 0,
            "time_range": None,
            "memory_mb": 0.0,
            "last_pull_time": None,
        }

        if self.cache_df is not None and not self.cache_df.empty:
            stats["total_samples"] = len(self.cache_df)
            stats["time_range"] = {
                "start": self.cache_df['timestamp'].min(),
                "end": self.cache_df['timestamp'].max(),
            }
            stats["memory_mb"] = self.cache_df.memory_usage(deep=True).sum() / 1024 / 1024

        if self.last_pull_time is not None:
            stats["last_pull_time"] = self.last_pull_time.strftime("%Y-%m-%d %H:%M:%S")

        return stats

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract feature matrix from DataFrame.

        Args:
            df: DataFrame containing sensor data.

        Returns:
            Feature matrix, shape=(n_samples, n_features).
        """
        if df.empty:
            return np.array([])

        # Select feature columns and convert to numpy array
        feature_columns = [
            "temperature",
            "humidity", 
            "brightness",
            "light_th",
            "light_cu",
            "curtain_status",
        ]

        # Ensure all columns exist
        missing_cols = set(feature_columns) - set(df.columns)
        if missing_cols:
            logger.warning("DataFrame is missing columns: %s", missing_cols)
            # Fill missing columns
            for col in missing_cols:
                df[col] = 0.0

        features = df[feature_columns].values
        return features

    def get_latest_samples(self, n_samples: int = 10) -> Optional[np.ndarray]:
        """Get the feature matrix of the latest N samples.

        Args:
            n_samples: Number of samples.

        Returns:
            Feature matrix, shape=(n_samples, n_features).
            Returns None if insufficient cached data.
        """
        if self.cache_df is None or len(self.cache_df) < n_samples:
            logger.warning("Insufficient cached data, need %d records, have %d records", 
                          n_samples, len(self.cache_df) if self.cache_df is not None else 0)
            return None

        # Get the latest N samples
        latest_df = self.cache_df.tail(n_samples)
        features = self.prepare_features(latest_df)

        return features
