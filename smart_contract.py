# smart_contract.py
import hashlib

class VotingContract:

    def __init__(self, db_connection):
        self.db = db_connection

    def hash_voter_id(self, voter_id):
        return hashlib.sha256(voter_id.encode()).hexdigest()

    def is_election_active(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT is_active FROM election_status WHERE id = 1")
        result = cursor.fetchone()
        cursor.close()
        print("Election active status:", result)  # Debug
        return result[0] if result else False

    def is_voter_registered(self, voter_id):
        cursor = self.db.cursor()
        print("Checking voter_id in DB:", voter_id)  # Debug
        cursor.execute(
            "SELECT id FROM voters WHERE voter_id = %s",
            (voter_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        print("Voter found in DB:", result)  # Debug
        return result is not None

    def has_already_voted(self, voter_id):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT has_voted FROM voters WHERE voter_id = %s",
            (voter_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        print("Has already voted:", result)  # Debug
        return result[0] if result else False

    def is_valid_candidate(self, candidate_id):
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT id FROM candidates WHERE id = %s",
            (candidate_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        print("Candidate valid:", result)  # Debug
        return result is not None

    def cast_vote(self, voter_id, candidate_id):
        print("=== SMART CONTRACT DEBUG ===")
        print("Voter ID received:", voter_id)
        print("Candidate ID received:", candidate_id)

        if not self.is_election_active():
            return {
                "success": False,
                "message": "Election is not currently active!"
            }

        if not self.is_voter_registered(voter_id):
            return {
                "success": False,
                "message": "You are not a registered voter!"
            }

        if self.has_already_voted(voter_id):
            return {
                "success": False,
                "message": "You have already cast your vote!"
            }

        if not self.is_valid_candidate(candidate_id):
            return {
                "success": False,
                "message": "Invalid candidate selected!"
            }

        return {
            "success": True,
            "message": "Vote approved!",
            "voter_hash": self.hash_voter_id(voter_id)
        }

    def mark_voter_as_voted(self, voter_id):
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE voters SET has_voted = TRUE WHERE voter_id = %s",
            (voter_id,)
        )
        self.db.commit()
        cursor.close()

    def update_candidate_vote_count(self, candidate_id):
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE candidates SET vote_count = vote_count + 1 WHERE id = %s",
            (candidate_id,)
        )
        self.db.commit()
        cursor.close()