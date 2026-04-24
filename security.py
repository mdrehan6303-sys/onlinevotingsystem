# security.py
import hashlib
from flask_bcrypt import Bcrypt
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from datetime import datetime
from app_db import get_db # We will create a local db helper to avoid circular imports

class SecurityModule:

    def __init__(self, app):
        self.bcrypt = Bcrypt(app)
        
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.dbscan = DBSCAN(eps=0.5, min_samples=2)
        self.alert_history = []
        
        self._load_training_data()

    def _load_training_data(self):
        """
        Loads baseline normal synthetic data and real DB data.
        """
        training_data = []

        # Synthetic normal baselines
        for _ in range(40): training_data.append([np.random.randint(9, 11), np.random.randint(0, 59), 1])
        for _ in range(10): training_data.append([np.random.randint(12, 13), np.random.randint(0, 59), 1])
        for _ in range(25): training_data.append([np.random.randint(14, 16), np.random.randint(0, 59), 1])
        for _ in range(35): training_data.append([np.random.randint(18, 20), np.random.randint(0, 59), 1])

        self.training_data = np.array(training_data)

        # Attempt to load historical logs from DB to train if available
        try:
            db = get_db()
            cursor = db.cursor(buffered=True)
            cursor.execute("SELECT hour, minute, voter_hash_segment FROM ai_voting_logs")
            historical = cursor.fetchall()
            cursor.close()
            
            if historical:
                real_data = np.array([[row[0], row[1], row[2]] for row in historical])
                self.training_data = np.vstack([self.training_data, real_data])
        except Exception as e:
            print("Notice: Could not load historical AI logs yet:", e)
            
        self.isolation_forest.fit(self.training_data)
        print("✅ AI anomaly detection models trained successfully!")

    def hash_password(self, password):
        """Hash password using Bcrypt (slow, secure algorithm)"""
        return self.bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, plain_password, hashed_password):
        """Verify entered password against stored Bcrypt hash"""
        try:
            return self.bcrypt.check_password_hash(hashed_password, plain_password)
        except ValueError:
            # Fallback if old SHA-256 hashes exist in DB
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

    def hash_voter_identity(self, voter_id):
        """Hide voter identity using SHA-256 for public ledger"""
        return hashlib.sha256(voter_id.encode()).hexdigest()

    def log_voting_activity(self, voter_id, ip_address=None):
        """Record when each vote happens for anomaly detection into DB"""
        now = datetime.now()
        voter_int = hash(voter_id) % 1000

        try:
            db = get_db()
            cursor = db.cursor(buffered=True)
            cursor.execute("""
                INSERT INTO ai_voting_logs (hour, minute, voter_hash_segment) VALUES (%s, %s, %s)
            """, (now.hour, now.minute, voter_int))
            
            if ip_address:
                cursor.execute("""
                    INSERT INTO ai_ip_logs (ip_address, attempt_time) VALUES (%s, %s)
                """, (ip_address, now))
            
            db.commit()
            cursor.close()
        except Exception as e:
            print(f"Error logging AI activity: {e}")

        # Retrain online with this new vote
        self._load_training_data()

    def detect_anomalies(self):
        try:
            db = get_db()
            cursor = db.cursor(buffered=True)
            
            # Check IP anomalies
            cursor.execute("""
                SELECT ip_address, COUNT(*) as cnt FROM ai_ip_logs 
                WHERE attempt_time > NOW() - INTERVAL 1 HOUR
                GROUP BY ip_address HAVING cnt >= 3
            """)
            ip_anomalies = cursor.fetchall()
            if ip_anomalies:
                for ip in ip_anomalies:
                    self._add_alert(f"Multiple rapid votes from IP: {ip[0]}")
                cursor.close()
                return "suspicious"

            # Check isolation forest
            cursor.execute("SELECT hour, minute, voter_hash_segment FROM ai_voting_logs ORDER BY id DESC LIMIT 50")
            recent_logs = cursor.fetchall()
            cursor.close()
            
            if len(recent_logs) < 3:
                return "insufficient data"
                
            real_data = np.array([[r[0], r[1], r[2]] for r in recent_logs])
            predictions = self.isolation_forest.predict(real_data)
            
            suspicious_count = list(predictions).count(-1)
            total_votes = len(recent_logs)
            
            if total_votes > 0 and suspicious_count / total_votes > 0.3: # Trigger warning if > 30% anomalous
                self._add_alert("High suspicious vote rate detected in last 50 votes!")
                return "suspicious"
            
            midnight_votes = sum(1 for log in recent_logs if log[0] < 6 or log[0] > 22)
            if midnight_votes > 0:
                self._add_alert(f"{midnight_votes} recent votes detected at unusual hours!")
                return "suspicious"

            return "normal"
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return "insufficient data"

    def _add_alert(self, message):
        alert = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message
        }
        self.alert_history.append(alert)
        if len(self.alert_history) > 50:
             self.alert_history.pop(0)

    def get_alerts(self):
        return self.alert_history