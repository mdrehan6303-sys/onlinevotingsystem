# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from blockchain import Blockchain
from smart_contract import VotingContract
from security import SecurityModule
from otp_service import OTPService

app = Flask(__name__)
app.secret_key = "voting_system_secret_key_2024"

blockchain = Blockchain()
security   = SecurityModule()
otp_service = OTPService()

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="voting_system"
    )

# ─────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ─────────────────────────────────────────
# VOTER REGISTRATION
# ─────────────────────────────────────────
@app.route("/voter/register", methods=["GET", "POST"])
def voter_register():
    if request.method == "POST":
        full_name = request.form["full_name"]
        voter_id  = request.form["voter_id"]
        email     = request.form["email"]
        password  = request.form["password"]

        # Check if voter already exists
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "SELECT id FROM voters WHERE voter_id = %s OR email = %s",
                (voter_id, email)
            )
            existing = cursor.fetchone()
            cursor.close()
            db.close()

            if existing:
                flash("Voter ID or Email already registered!", "error")
                return render_template("voter_register.html")

        except Exception as e:
            flash("Database error: " + str(e), "error")
            return render_template("voter_register.html")

        # Store registration data temporarily in session
        # We save this until OTP is verified
        session["temp_registration"] = {
            "full_name": full_name,
            "voter_id":  voter_id,
            "email":     email,
            "password":  security.hash_password(password)
        }

        # Generate and send OTP
        print(f"Sending OTP to {email}")
        success = otp_service.generate_and_send(email, full_name)

        if success:
            flash("OTP sent to your email! Please verify.", "success")
            return redirect(url_for("verify_otp"))
        else:
            flash("Failed to send OTP. Check your email address!", "error")

    return render_template("voter_register.html")

# ─────────────────────────────────────────
# VERIFY OTP PAGE
# ─────────────────────────────────────────
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    # Check if there is registration data in session
    if "temp_registration" not in session:
        flash("Please register first!", "error")
        return redirect(url_for("voter_register"))

    email = session["temp_registration"]["email"]

    if request.method == "POST":
        entered_otp = request.form["otp"]
        print(f"OTP entered: {entered_otp}")

        result = otp_service.verify_otp(email, entered_otp)
        print(f"OTP verification result: {result}")

        if result == "valid":
            # OTP correct — save voter to database
            data = session["temp_registration"]

            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO voters
                    (full_name, voter_id, email, password)
                    VALUES (%s, %s, %s, %s)
                """, (
                    data["full_name"],
                    data["voter_id"],
                    data["email"],
                    data["password"]
                ))
                db.commit()
                cursor.close()
                db.close()

                # Clear temporary registration data
                session.pop("temp_registration", None)

                flash("Email verified! Registration successful! Please login.", "success")
                return redirect(url_for("voter_login"))

            except Exception as e:
                flash("Error saving registration: " + str(e), "error")

        elif result == "expired":
            flash("OTP has expired! Please register again.", "error")
            session.pop("temp_registration", None)
            return redirect(url_for("voter_register"))

        elif result == "invalid":
            flash("Wrong OTP! Please try again.", "error")

        else:
            flash("OTP not found! Please register again.", "error")
            return redirect(url_for("voter_register"))

    return render_template("verify_otp.html", email=email)

# ─────────────────────────────────────────
# RESEND OTP
# ─────────────────────────────────────────
@app.route("/resend-otp")
def resend_otp():
    if "temp_registration" not in session:
        flash("Please register first!", "error")
        return redirect(url_for("voter_register"))

    data  = session["temp_registration"]
    email = data["email"]
    name  = data["full_name"]

    success = otp_service.generate_and_send(email, name)

    if success:
        flash("New OTP sent to your email!", "success")
    else:
        flash("Failed to send OTP. Try again!", "error")

    return redirect(url_for("verify_otp"))

# ─────────────────────────────────────────
# VOTER LOGIN
# ─────────────────────────────────────────
@app.route("/voter/login", methods=["GET", "POST"])
def voter_login():
    if request.method == "POST":
        voter_id = request.form["voter_id"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM voters WHERE voter_id = %s",
            (voter_id,)
        )
        voter = cursor.fetchone()
        cursor.close()
        db.close()

        print("=== LOGIN DEBUG ===")
        print("Voter ID entered:", voter_id)
        print("Voter found:", voter)

        if voter and security.verify_password(password, voter[4]):
            # Store voter details in session
            session["voter_id"]   = voter[2]
            session["voter_name"] = voter[1]
            print("Session voter_id:", session["voter_id"])
            flash("Login successful! Welcome " + voter[1], "success")
            return redirect(url_for("vote"))
        else:
            flash("Invalid Voter ID or Password!", "error")

    return render_template("voter_login.html")

# ─────────────────────────────────────────
# CAST VOTE
# ─────────────────────────────────────────
@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "voter_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("voter_login"))

    db = get_db()

    if request.method == "POST":
        candidate_id = int(request.form["candidate_id"])
        voter_id     = session["voter_id"]

        print("=== VOTE DEBUG ===")
        print("Voter ID from session:", voter_id)
        print("Candidate ID:", candidate_id)

        contract = VotingContract(db)
        result   = contract.cast_vote(voter_id, candidate_id)

        print("Smart contract result:", result)

        if result["success"]:
            new_block = blockchain.add_vote(
                voter_hash   = result["voter_hash"],
                candidate_id = candidate_id
            )

            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO blockchain_votes
                (block_index, voter_hash, candidate_id,
                 timestamp, previous_hash, current_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                new_block.index,
                new_block.voter_hash,
                new_block.candidate_id,
                new_block.timestamp,
                new_block.previous_hash,
                new_block.current_hash
            ))
            db.commit()
            cursor.close()

            contract.mark_voter_as_voted(voter_id)
            contract.update_candidate_vote_count(candidate_id)
            security.log_voting_activity(voter_id)

            db.close()
            flash("Your vote has been cast successfully! 🎉", "success")
            return redirect(url_for("index"))
        else:
            flash(result["message"], "error")

    cursor = db.cursor()
    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("vote.html", candidates=candidates)

# ─────────────────────────────────────────
# VOTER LOGOUT
# ─────────────────────────────────────────
@app.route("/voter/logout")
def voter_logout():
    session.pop("voter_id", None)
    session.pop("voter_name", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("index"))

# ─────────────────────────────────────────
# ADMIN LOGIN
# ─────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM admin WHERE username = %s AND password = %s",
            (username, password)
        )
        admin = cursor.fetchone()
        cursor.close()
        db.close()

        if admin:
            session["admin"] = username
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials!", "error")

    return render_template("admin_login.html")

# ─────────────────────────────────────────
# ADMIN DASHBOARD
# ─────────────────────────────────────────
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        flash("Please login as admin!", "error")
        return redirect(url_for("admin_login"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM voters")
    total_voters = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM voters WHERE has_voted = TRUE")
    votes_cast = cursor.fetchone()[0]

    cursor.execute("SELECT is_active FROM election_status WHERE id = 1")
    election_active = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM candidates ORDER BY vote_count DESC")
    candidates = cursor.fetchall()

    cursor.close()
    db.close()

    chain_valid    = blockchain.is_chain_valid()
    anomaly_status = security.detect_anomalies()
    alerts         = security.get_alerts()

    return render_template("admin_dashboard.html",
        total_voters    = total_voters,
        votes_cast      = votes_cast,
        election_active = election_active,
        candidates      = candidates,
        chain_valid     = chain_valid,
        anomaly_status  = anomaly_status,
        alerts          = alerts
    )
# ─────────────────────────────────────────
# START / STOP ELECTION
# ─────────────────────────────────────────
@app.route("/admin/toggle_election")
def toggle_election():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT is_active FROM election_status WHERE id = 1")
    current = cursor.fetchone()[0]

    cursor.execute(
        "UPDATE election_status SET is_active = %s WHERE id = 1",
        (not current,)
    )
    db.commit()
    cursor.close()
    db.close()

    status = "started" if not current else "stopped"
    flash(f"Election has been {status}!", "success")
    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# RESULTS PAGE
# ─────────────────────────────────────────
@app.route("/results")
def results():
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM candidates ORDER BY vote_count DESC"
    )
    candidates = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM voters WHERE has_voted = TRUE"
    )
    total_votes = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return render_template("results.html",
        candidates  = candidates,
        total_votes = total_votes
    )

# ─────────────────────────────────────────
# ADMIN LOGOUT
# ─────────────────────────────────────────
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Admin logged out!", "success")
    return redirect(url_for("index"))

# ─────────────────────────────────────────
# RUN THE APP
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)