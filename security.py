# security.py
import hashlib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from datetime import datetime
import json

class SecurityModule:

    def __init__(self):
        # Isolation Forest model
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42
        )

        # DBSCAN model
        self.dbscan = DBSCAN(
            eps=0.5,
            min_samples=2
        )

        # Store voting logs
        self.voting_logs   = []
        self.ip_logs       = {}
        self.alert_history = []

        # Pre-load realistic training data
        self._load_training_data()

    def _load_training_data(self):
        """
        Load realistic voting pattern data to train AI models.
        This represents normal voting behavior throughout a day.
        Normal peaks: 9-11 AM, 2-4 PM, 6-8 PM
        """
        training_data = []

        # Morning rush 9AM - 11AM (peak voting time)
        for _ in range(40):
            hour   = np.random.randint(9, 11)
            minute = np.random.randint(0, 59)
            training_data.append([hour, minute, 1])

        # Lunch time 12PM - 1PM (low voting)
        for _ in range(10):
            hour   = np.random.randint(12, 13)
            minute = np.random.randint(0, 59)
            training_data.append([hour, minute, 1])

        # Afternoon 2PM - 4PM (medium voting)
        for _ in range(25):
            hour   = np.random.randint(14, 16)
            minute = np.random.randint(0, 59)
            training_data.append([hour, minute, 1])

        # Evening rush 6PM - 8PM (peak voting time)
        for _ in range(35):
            hour   in range(18, 20)
            hour   = np.random.randint(18, 20)
            minute = np.random.randint(0, 59)
            training_data.append([hour, minute, 1])

        # Store as numpy array
        self.training_data = np.array(training_data)

        # Train models on realistic data
        self.isolation_forest.fit(self.training_data)
        print("✅ AI anomaly detection models trained successfully!")

    # ─────────────────────────────────────────
    # PASSWORD HASHING
    # ─────────────────────────────────────────

    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, plain_password, hashed_password):
        """Verify entered password against stored hash"""
        return self.hash_password(plain_password) == hashed_password

    def hash_voter_identity(self, voter_id):
        """Hide voter identity using SHA-256"""
        return hashlib.sha256(voter_id.encode()).hexdigest()

    # ─────────────────────────────────────────
    # VOTING ACTIVITY LOGGING
    # ─────────────────────────────────────────

    def log_voting_activity(self, voter_id, ip_address=None):
        """
        Record when each vote happens.
        Tracks time and IP address for anomaly detection.
        """
        now = datetime.now()

        # Add to voting logs
        self.voting_logs.append([
            now.hour,
            now.minute,
            hash(voter_id) % 1000
        ])

        # Track IP addresses
        if ip_address:
            if ip_address not in self.ip_logs:
                self.ip_logs[ip_address] = []
            self.ip_logs[ip_address].append(now)

        print(f"Vote logged at {now.hour}:{now.minute:02d}")

    # ─────────────────────────────────────────
    # ANOMALY DETECTION
    # ─────────────────────────────────────────

    def detect_anomalies(self):
        """
        Uses AI to detect suspicious voting patterns.
        Combines training data with real voting logs.

        Returns:
        - normal       → Everything looks fine ✅
        - suspicious   → Unusual pattern detected 🚨
        - insufficient → Not enough data yet
        """
        # Check IP based anomalies first
        ip_anomaly = self._check_ip_anomalies()
        if ip_anomaly:
            return "suspicious"

        # Need at least 3 real votes to analyze
        if len(self.voting_logs) < 3:
            return "insufficient data"

        try:
            # Combine training data with real votes
            real_data = np.array(self.voting_logs)
            combined  = np.vstack([self.training_data, real_data])

            # Retrain with combined data
            self.isolation_forest.fit(combined)

            # Predict on real votes only
            predictions = self.isolation_forest.predict(real_data)

            # Count suspicious votes
            suspicious_count = list(predictions).count(-1)
            total_votes      = len(self.voting_logs)

            print(f"Anomaly check: {suspicious_count}/{total_votes} suspicious")

            # If more than 20% votes are suspicious
            if suspicious_count / total_votes > 0.2:
                self._add_alert("High suspicious vote rate detected!")
                return "suspicious"

            # Check for unusual voting hours (midnight votes)
            midnight_votes = sum(
                1 for log in self.voting_logs
                if log[0] < 6 or log[0] > 22
            )

            if midnight_votes > 0:
                self._add_alert(
                    f"{midnight_votes} votes detected at unusual hours!"
                )
                return "suspicious"

            return "normal"

        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return "insufficient data"

    def _check_ip_anomalies(self):
        """
        Check if any IP address is voting too many times.
        More than 3 votes from same IP = suspicious!
        """
        for ip, times in self.ip_logs.items():
            if len(times) >= 3:
                self._add_alert(
                    f"Multiple votes from IP: {ip}"
                )
                return True
        return False

    def _add_alert(self, message):
        """Add alert to history"""
        alert = {
            "time":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message
        }
        self.alert_history.append(alert)
        print(f"🚨 ALERT: {message}")

    def get_alerts(self):
        """Get all security alerts"""
        return self.alert_history

    def get_voting_stats(self):
        """
        Get statistics about voting patterns.
        Used to display charts in admin dashboard.
        """
        if not self.voting_logs:
            return {
                "total_votes":    0,
                "peak_hour":      "No data",
                "hourly_counts":  {},
                "anomaly_status": "insufficient data"
            }

        # Count votes per hour
        hourly_counts = {}
        for log in self.voting_logs:
            hour = log[0]
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

        # Find peak voting hour
        peak_hour = max(hourly_counts, key=hourly_counts.get)

        return {
            "total_votes":    len(self.voting_logs),
            "peak_hour":      f"{peak_hour}:00",
            "hourly_counts":  hourly_counts,
            "anomaly_status": self.detect_anomalies()
        }

    # ─────────────────────────────────────────
    # RATE LIMITING
    # ─────────────────────────────────────────

    def is_rate_limited(self, ip_address, request_times):
        """
        Prevent brute force attacks.
        Block IP if more than 5 attempts in 60 seconds.
        """
        now = datetime.now()

        recent = [
            t for t in request_times.get(ip_address, [])
            if (now - t).seconds < 60
        ]

        if len(recent) >= 5:
            return True

        return False