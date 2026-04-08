# security.py
# This file handles all security features:
# 1. Password hashing using SHA-256
# 2. Anomaly detection using DBSCAN and Isolation Forest

import hashlib                                    # For SHA-256 hashing
import numpy as np                                # For mathematical operations
from sklearn.ensemble import IsolationForest      # AI anomaly detection
from sklearn.cluster import DBSCAN                # AI clustering algorithm
from datetime import datetime                     # For tracking vote times

class SecurityModule:
    """
    SecurityModule protects our voting system from:
    1. Password theft (using SHA hashing)
    2. Suspicious voting patterns (using AI detection)
    """

    def __init__(self):
        """
        Initialize the anomaly detection models.
        These AI models learn what 'normal' voting looks like
        and alert us when something unusual happens.
        """
        # Isolation Forest — detects outliers (unusual behavior)
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expects 10% of data might be suspicious
            random_state=42
        )

        # DBSCAN — groups similar voting patterns together
        self.dbscan = DBSCAN(
            eps=0.5,        # How close patterns must be to form a group
            min_samples=2   # Minimum votes needed to form a group
        )

        # Store voting activity logs for analysis
        # Each entry = [hour_of_day, minute_of_vote]
        self.voting_logs = []

    # ─────────────────────────────────────────
    # JOB 1: PASSWORD HASHING
    # ─────────────────────────────────────────

    def hash_password(self, password):
        """
        Converts a plain password into a secure hash.
        
        Example:
        Input:  "mypassword123"
        Output: "ef92b778bafe771204..." (unreadable!)
        
        This is ONE-WAY — you cannot reverse it back to original!
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, plain_password, hashed_password):
        """
        Checks if a entered password matches the stored hash.
        
        We hash the entered password and compare it to stored hash.
        If they match → password is correct!
        If they don't → wrong password!
        
        We NEVER store the original password — only the hash!
        """
        return self.hash_password(plain_password) == hashed_password

    def hash_voter_identity(self, voter_id):
        """
        Hides voter identity using SHA-256.
        This is stored in blockchain instead of real voter ID
        to protect voter privacy.
        """
        return hashlib.sha256(voter_id.encode()).hexdigest()

    # ─────────────────────────────────────────
    # JOB 2: ANOMALY DETECTION
    # ─────────────────────────────────────────

    def log_voting_activity(self, voter_id):
        """
        Records when each vote happens.
        We store the hour and minute of each vote.
        
        Example:
        Vote at 2:30 PM → stored as [14, 30]
        Vote at 2:31 PM → stored as [14, 31]
        
        If 100 votes happen at 2:30 PM → SUSPICIOUS! 🚨
        """
        now = datetime.now()
        self.voting_logs.append([
            now.hour,           # Hour of vote (0-23)
            now.minute,         # Minute of vote (0-59)
            hash(voter_id) % 1000  # Anonymized voter identifier
        ])

    def detect_anomalies(self):
        """
        Uses AI to detect suspicious voting patterns.
        
        Returns:
        - "normal"    → Everything looks fine ✅
        - "suspicious" → Unusual pattern detected 🚨
        - "insufficient data" → Not enough votes yet to analyze
        """
        # Need at least 10 votes to start detecting patterns
        if len(self.voting_logs) < 10:
            return "insufficient data"

        # Convert logs to numpy array for AI processing
        data = np.array(self.voting_logs)

        # ── Isolation Forest Detection ──
        # Trains on voting data and predicts which are outliers
        iso_predictions = self.isolation_forest.fit_predict(data)
        # -1 means suspicious/outlier, 1 means normal
        suspicious_iso = list(iso_predictions).count(-1)

        # ── DBSCAN Detection ──
        # Groups votes into clusters — votes far from any cluster are suspicious
        db_predictions = self.dbscan.fit_predict(data)
        # -1 means the vote doesn't belong to any normal cluster
        suspicious_db = list(db_predictions).count(-1)

        # If more than 20% votes are flagged as suspicious → alert!
        total_votes = len(self.voting_logs)
        if (suspicious_iso / total_votes > 0.2 or
                suspicious_db / total_votes > 0.2):
            return "suspicious"

        return "normal"

    def is_rate_limited(self, ip_address, request_times):
        """
        Prevents brute force attacks.
        
        If someone tries to login more than 5 times in 1 minute
        from the same IP address → block them temporarily!
        
        Think of it like a lock that blocks after 5 wrong attempts.
        """
        now = datetime.now()

        # Count requests from this IP in last 60 seconds
        recent_requests = [
            t for t in request_times.get(ip_address, [])
            if (now - t).seconds < 60
        ]

        # If more than 5 attempts in 60 seconds → rate limit!
        if len(recent_requests) >= 5:
            return True  # Block this IP temporarily

        return False  # Allow the request
