from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO
import mysql.connector
from blockchain import Blockchain
from security import SecurityModule
from otp_service import OTPService
from datetime import datetime
import os
import csv
import io
from app_db import get_db, close_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "voting_system_secret_key_2024")
app.teardown_appcontext(close_db)

socketio = SocketIO(app, cors_allowed_origins="*")

with app.app_context():
    security    = SecurityModule(app)
otp_service = OTPService()

# Each election has its own blockchain
election_blockchains = {}

# Db handled by app_db

def get_blockchain(election_id):
    """Get or create blockchain and restore past blocks"""
    if election_id not in election_blockchains:
        chain = Blockchain()
        try:
            db = get_db()
            cursor = db.cursor(buffered=True)
            cursor.execute("SELECT block_index, voter_hash, candidate_id, previous_hash, timestamp, current_hash FROM election_blockchain_votes WHERE election_id = %s ORDER BY block_index ASC", (election_id,))
            blocks = cursor.fetchall()
            for b in blocks:
                chain.restore_block(b[0], b[1], b[2], b[3], b[4], b[5])
            cursor.close()
        except Exception:
            pass
        election_blockchains[election_id] = chain
    return election_blockchains[election_id]

# ─────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────
@app.route("/")
def index():
    db = get_db()
    cursor = db.cursor(buffered=True)

    # Get all active elections
    cursor.execute("""
        SELECT id, title, description, start_time, end_time, is_active
        FROM elections
        ORDER BY created_at DESC
    """)
    elections = cursor.fetchall()
    cursor.close()
    # db.close() handled by teardown

    return render_template("index.html", elections=elections)

# ─────────────────────────────────────────
# SELECT ELECTION
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>")
def election_home(election_id):
    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute(
        "SELECT * FROM elections WHERE id = %s",
        (election_id,)
    )
    election = cursor.fetchone()

    if not election:
        flash("Election not found!", "error")
        return redirect(url_for("index"))

    cursor.execute(
        "SELECT id, name, party, vote_count FROM election_candidates WHERE election_id = %s ORDER BY vote_count DESC",
        (election_id,)
    )
    candidates = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM election_voters WHERE election_id = %s",
        (election_id,)
    )
    total_voters = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM election_voters WHERE election_id = %s AND has_voted = TRUE",
        (election_id,)
    )
    votes_cast = cursor.fetchone()[0]

    cursor.close()
    # db.close() handled by teardown

    results_released = election[7] if len(election) > 7 else False

    return render_template("election_home.html",
        election          = election,
        candidates        = candidates,
        total_voters      = total_voters,
        votes_cast        = votes_cast,
        election_id       = election_id,
        results_released  = results_released
    )

# ─────────────────────────────────────────
# VOTER REGISTRATION
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/register", methods=["GET", "POST"])
def voter_register(election_id):
    db = get_db()
    cursor = db.cursor(buffered=True)

    # Get election details
    cursor.execute(
        "SELECT * FROM elections WHERE id = %s",
        (election_id,)
    )
    election = cursor.fetchone()

    if request.method == "POST":
        full_name     = request.form["full_name"]
        voter_id      = request.form["voter_id"]
        email         = request.form["email"]
        aadhar_number = request.form["aadhar_number"]
        phone         = request.form["phone"]
        dob           = request.form["date_of_birth"]
        password      = request.form["password"]

        # Step 1: Check if voter exists in approved list
        cursor.execute("""
            SELECT * FROM approved_voters
            WHERE voter_id = %s
            AND email = %s
            AND aadhar_number = %s
            AND phone = %s
            AND election_id = %s
        """, (voter_id, email, aadhar_number, phone, election_id))

        approved = cursor.fetchone()

        if not approved:
            flash("Your details do not match our records! You are not an approved voter.", "error")
            cursor.close()
            # db.close() handled by teardown
            return render_template("voter_register.html",
                election=election,
                election_id=election_id
            )

        # Step 2: Check if already registered for this election
        cursor.execute("""
            SELECT id FROM election_voters
            WHERE election_id = %s AND voter_id = %s
        """, (election_id, voter_id))

        already_registered = cursor.fetchone()

        if already_registered:
            flash("You are already registered for this election!", "error")
            cursor.close()
            # db.close() handled by teardown
            return render_template("voter_register.html",
                election=election,
                election_id=election_id
            )

        cursor.close()
        # db.close() handled by teardown

        # Step 3: Store temp data and send OTP
        session["temp_registration"] = {
            "full_name":    full_name,
            "voter_id":     voter_id,
            "email":        email,
            "aadhar":       aadhar_number,
            "phone":        phone,
            "dob":          dob,
            "password":     security.hash_password(password),
            "election_id":  election_id
        }

        success = otp_service.generate_and_send(email, full_name)

        if success:
            flash("OTP sent to your email!", "success")
            return redirect(url_for("verify_otp",
                election_id=election_id))
        else:
            flash("Failed to send OTP!", "error")

    else:
        cursor.close()
        # db.close() handled by teardown

    return render_template("voter_register.html",
        election=election,
        election_id=election_id
    )

# ─────────────────────────────────────────
# VERIFY OTP
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/verify-otp",
           methods=["GET", "POST"])
def verify_otp(election_id):
    if "temp_registration" not in session:
        flash("Please register first!", "error")
        return redirect(url_for("voter_register",
            election_id=election_id))

    email = session["temp_registration"]["email"]

    if request.method == "POST":
        entered_otp = request.form["otp"]
        result      = otp_service.verify_otp(email, entered_otp)

        if result == "valid":
            data = session["temp_registration"]
            eid  = data["election_id"]

            try:
                db = get_db()
                cursor = db.cursor(buffered=True)

                cursor.execute("""
                    INSERT INTO election_voters
                    (election_id, voter_id, full_name, email, password)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    eid,
                    data["voter_id"],
                    data["full_name"],
                    data["email"],
                    data["password"]
                ))
                db.commit()
                cursor.close()
                # db.close() handled by teardown

                session.pop("temp_registration", None)
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("voter_login",
                    election_id=eid))

            except Exception as e:
                flash("Error: " + str(e), "error")

        elif result == "expired":
            flash("OTP expired! Please register again.", "error")
            session.pop("temp_registration", None)
            return redirect(url_for("voter_register",
                election_id=election_id))

        elif result == "invalid":
            flash("Wrong OTP! Try again.", "error")

        else:
            flash("OTP not found!", "error")

    return render_template("verify_otp.html",
        email=email,
        election_id=election_id
    )

# ─────────────────────────────────────────
# RESEND OTP
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/resend-otp")
def resend_otp(election_id):
    if "temp_registration" not in session:
        return redirect(url_for("voter_register",
            election_id=election_id))

    data  = session["temp_registration"]
    success = otp_service.generate_and_send(
        data["email"], data["full_name"]
    )

    if success:
        flash("New OTP sent!", "success")
    else:
        flash("Failed to send OTP!", "error")

    return redirect(url_for("verify_otp",
        election_id=election_id))

# ─────────────────────────────────────────
# VOTER LOGIN
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/login",
           methods=["GET", "POST"])
def voter_login(election_id):
    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute(
        "SELECT * FROM elections WHERE id = %s",
        (election_id,)
    )
    election = cursor.fetchone()

    if request.method == "POST":
        voter_id = request.form["voter_id"]
        password = request.form["password"]
        biometric_data = request.form.get("biometric_data", "")

        cursor.execute("""
            SELECT * FROM election_voters
            WHERE election_id = %s AND voter_id = %s
        """, (election_id, voter_id))

        voter = cursor.fetchone()

        if voter and security.verify_password(password, voter[5]):
            # Save biometric checkpoint
            if biometric_data:
                cursor.execute("UPDATE election_voters SET biometric_data = %s WHERE id = %s", (biometric_data, voter[0]))
                db.commit()

            cursor.close()
            # db.close() handled by teardown
            session["voter_id"]     = voter[2]  # voter_id is index 2 in our schema! Wait, old schema had it at 3? Let me double-check
            session["voter_name"]   = voter[3]
            session["election_id"]  = election_id
            flash("Login successful! Welcome " + voter[3], "success")
            return redirect(url_for("vote",
                election_id=election_id))
        else:
            flash("Invalid Voter ID or Password!", "error")
    else:
        cursor.close()
        # db.close() handled by teardown

    return render_template("voter_login.html",
        election=election,
        election_id=election_id
    )

# ─────────────────────────────────────────
# CAST VOTE
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/vote",
           methods=["GET", "POST"])
def vote(election_id):
    if "voter_id" not in session or \
       session.get("election_id") != election_id:
        flash("Please login first!", "error")
        return redirect(url_for("voter_login",
            election_id=election_id))

    db = get_db()

    # Check election is active
    cursor = db.cursor(buffered=True)
    cursor.execute(
        "SELECT is_active, end_time FROM elections WHERE id = %s",
        (election_id,)
    )
    election_data = cursor.fetchone()

    # Auto stop election if time expired
    if election_data[1] and datetime.now() > election_data[1]:
        cursor.execute(
            "UPDATE elections SET is_active = FALSE WHERE id = %s",
            (election_id,)
        )
        db.commit()
        cursor.close()
        # db.close() handled by teardown
        flash("Election has ended!", "error")
        return redirect(url_for("election_home",
            election_id=election_id))

    if request.method == "POST":
        candidate_id = int(request.form["candidate_id"])
        voter_id     = session["voter_id"]
        voter_name   = session["voter_name"]

        # Check if already voted
        cursor.execute("""
            SELECT has_voted FROM election_voters
            WHERE election_id = %s AND voter_id = %s
        """, (election_id, voter_id))

        voter_data = cursor.fetchone()

        if voter_data and voter_data[0]:
            flash("You have already voted!", "error")
            cursor.close()
            # db.close() handled by teardown
            return redirect(url_for("election_home",
                election_id=election_id))

        # Check election active
        if not election_data[0]:
            flash("Election is not active!", "error")
            cursor.close()
            # db.close() handled by teardown
            return redirect(url_for("election_home",
                election_id=election_id))

        # Add vote to blockchain
        voter_hash = security.hash_voter_identity(voter_id)
        chain      = get_blockchain(election_id)
        new_block  = chain.add_vote(
            voter_hash   = voter_hash,
            candidate_id = candidate_id
        )

        # Save block to database
        cursor.execute("""
            INSERT INTO election_blockchain_votes
            (election_id, block_index, voter_hash,
             candidate_id, timestamp, previous_hash, current_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            election_id,
            new_block.index,
            new_block.voter_hash,
            new_block.candidate_id,
            new_block.timestamp,
            new_block.previous_hash,
            new_block.current_hash
        ))

        # Mark voter as voted
        cursor.execute("""
            UPDATE election_voters
            SET has_voted = TRUE
            WHERE election_id = %s AND voter_id = %s
        """, (election_id, voter_id))

        # Update candidate vote count
        cursor.execute("""
            UPDATE election_candidates
            SET vote_count = vote_count + 1
            WHERE id = %s AND election_id = %s
        """, (candidate_id, election_id))

        # Get candidate details for receipt
        cursor.execute(
            "SELECT name, party FROM election_candidates WHERE id = %s",
            (candidate_id,)
        )
        candidate = cursor.fetchone()

        db.commit()
        cursor.close()

        security.log_voting_activity(voter_id)
        # db.close() handled by teardown

        # ─── REALTIME WEBSOCKET EMIT ───
        socketio.emit("new_vote", {"election_id": election_id})

        # ─── QR CODE GENERATION ───
        import qrcode
        import io
        import base64

        qr_data = f"Election: {election_id}\nBlock: {new_block.index}\nHash: {new_block.current_hash}\nPrev: {new_block.previous_hash}\nVoter: {new_block.voter_hash}"
        qr = qrcode.make(qr_data)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        # Create receipt
        receipt = {
            "voter_name":      voter_name,
            "voter_id":        voter_id,
            "candidate_name":  candidate[0],
            "candidate_party": candidate[1],
            "block_index":     new_block.index,
            "current_hash":    new_block.current_hash,
            "previous_hash":   new_block.previous_hash,
            "voter_hash":      new_block.voter_hash,
            "timestamp":       datetime.now().strftime(
                "%d %B %Y at %I:%M %p"
            ),
            "election_id":     election_id,
            "qr_code":         qr_b64
        }

        return render_template("vote_receipt.html",
            receipt=receipt)

    # Get candidates for this election
    cursor.execute(
        "SELECT id, name, party, vote_count FROM election_candidates WHERE election_id = %s",
        (election_id,)
    )
    candidates = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM elections WHERE id = %s",
        (election_id,)
    )
    election = cursor.fetchone()

    cursor.close()
    # db.close() handled by teardown

    return render_template("vote.html",
        candidates  = candidates,
        election    = election,
        election_id = election_id
    )

# ─────────────────────────────────────────
# VOTER LOGOUT
# ─────────────────────────────────────────
@app.route("/voter/logout")
def voter_logout():
    election_id = session.get("election_id")
    session.pop("voter_id",    None)
    session.pop("voter_name",  None)
    session.pop("election_id", None)
    flash("Logged out!", "success")
    if election_id:
        return redirect(url_for("election_home",
            election_id=election_id))
    return redirect(url_for("index"))

# ─────────────────────────────────────────
# VOTER ID CARD
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/id-card")
def voter_id_card(election_id):
    if "voter_id" not in session:
        flash("Please login first!", "error")
        return redirect(url_for("voter_login",
            election_id=election_id))

    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT full_name, voter_id, email
        FROM election_voters
        WHERE election_id = %s AND voter_id = %s
    """, (election_id, session["voter_id"]))

    voter_data = cursor.fetchone()

    cursor.execute(
        "SELECT title FROM elections WHERE id = %s",
        (election_id,)
    )
    election = cursor.fetchone()

    cursor.close()
    # db.close() handled by teardown

    voter = {
        "full_name":    voter_data[0],
        "voter_id":     voter_data[1],
        "email":        voter_data[2],
        "issued_date":  datetime.now().strftime("%d %B %Y"),
        "election":     election[0]
    }

    return render_template("voter_id_card.html",
        voter=voter,
        election_id=election_id
    )

# ─────────────────────────────────────────
# RESULTS PAGE
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/results")
def results(election_id):
    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute(
        "SELECT * FROM elections WHERE id = %s",
        (election_id,)
    )
    election = cursor.fetchone()

    if not election:
        flash("Election not found!", "error")
        return redirect(url_for("index"))

    # Check if results are released — only admin can bypass
    is_admin = "admin" in session
    results_released = election[7] if len(election) > 7 else False

    if not results_released and not is_admin:
        flash("Results have not been released yet by the admin. Please wait!", "error")
        return redirect(url_for("election_home", election_id=election_id))

    cursor.execute("""
        SELECT id, name, party, vote_count FROM election_candidates
        WHERE election_id = %s
        ORDER BY vote_count DESC
    """, (election_id,))
    candidates = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) FROM election_voters
        WHERE election_id = %s AND has_voted = TRUE
    """, (election_id,))
    total_votes = cursor.fetchone()[0]

    cursor.close()
    # db.close() handled by teardown

    return render_template("results.html",
        candidates       = candidates,
        total_votes      = total_votes,
        election         = election,
        election_id      = election_id,
        results_released = results_released,
        is_admin         = is_admin
    )

# ─────────────────────────────────────────
# LIVE RESULTS API
# ─────────────────────────────────────────
@app.route("/api/live-results/<int:election_id>")
def live_results(election_id):
    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute("""
        SELECT id, name, party, vote_count
        FROM election_candidates
        WHERE election_id = %s
        ORDER BY vote_count DESC
    """, (election_id,))
    candidates = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) FROM election_voters
        WHERE election_id = %s AND has_voted = TRUE
    """, (election_id,))
    total_votes = cursor.fetchone()[0]

    cursor.execute(
        "SELECT is_active, end_time FROM elections WHERE id = %s",
        (election_id,)
    )
    election_data = cursor.fetchone()

    # Auto stop if time expired
    if election_data[1] and datetime.now() > election_data[1]:
        cursor.execute(
            "UPDATE elections SET is_active = FALSE WHERE id = %s",
            (election_id,)
        )
        db.commit()

    cursor.close()
    # db.close() handled by teardown

    candidates_data = []
    for c in candidates:
        percentage = 0
        if total_votes > 0:
            percentage = round(c[3] / total_votes * 100, 1)
        candidates_data.append({
            "id":         c[0],
            "name":       c[1],
            "party":      c[2],
            "votes":      c[3],
            "percentage": percentage
        })

    return jsonify({
        "candidates":      candidates_data,
        "total_votes":     total_votes,
        "election_active": bool(election_data[0]),
        "timestamp":       datetime.now().strftime(
            "%d %b %Y %I:%M:%S %p"
        )
    })

# ─────────────────────────────────────────
# STATISTICS
# ─────────────────────────────────────────
@app.route("/election/<int:election_id>/statistics")
def statistics(election_id):
    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute(
        "SELECT * FROM elections WHERE id = %s",
        (election_id,)
    )
    election = cursor.fetchone()

    if not election:
        flash("Election not found!", "error")
        return redirect(url_for("index"))

    # Block voters from statistics until results are released
    is_admin = "admin" in session
    results_released = election[7] if len(election) > 7 else False

    if not results_released and not is_admin:
        flash("Statistics will be available after the admin releases the results!", "error")
        return redirect(url_for("election_home", election_id=election_id))

    cursor.execute("""
        SELECT COUNT(*) FROM election_voters
        WHERE election_id = %s
    """, (election_id,))
    total_voters = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM election_voters
        WHERE election_id = %s AND has_voted = TRUE
    """, (election_id,))
    votes_cast = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM election_candidates
        WHERE election_id = %s
    """, (election_id,))
    total_candidates = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM election_blockchain_votes
        WHERE election_id = %s
    """, (election_id,))
    total_blocks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, name, party, vote_count FROM election_candidates
        WHERE election_id = %s
        ORDER BY vote_count DESC
    """, (election_id,))
    candidates = cursor.fetchall()

    cursor.close()
    # db.close() handled by teardown

    turnout = 0
    if total_voters > 0:
        turnout = round(votes_cast / total_voters * 100, 1)

    chain       = get_blockchain(election_id)
    chain_valid = chain.is_chain_valid()

    stats = {
        "total_voters":     total_voters,
        "votes_cast":       votes_cast,
        "total_candidates": total_candidates,
        "total_blocks":     total_blocks + 1,
        "turnout":          turnout,
        "chain_valid":      chain_valid,
        "candidates":       candidates
    }

    return render_template("statistics.html",
        stats       = stats,
        election    = election,
        election_id = election_id
    )

# ─────────────────────────────────────────
# ADMIN LOGIN
# ─────────────────────────────────────────
# ─────────────────────────────────────────
# ADMIN LOGIN
# ─────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute(
            "SELECT * FROM admin WHERE username = %s",
            (username,)
        )
        admin = cursor.fetchone()
        cursor.close()
        # db.close() handled by teardown

        if admin and security.verify_password(password, admin[2]):
            session.clear()
            session["admin"] = username
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials!", "error")

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
    cursor = db.cursor(buffered=True)

    # Get all elections
    cursor.execute("""
        SELECT e.*,
        (SELECT COUNT(*) FROM election_voters WHERE election_id = e.id) as total_voters,
        (SELECT COUNT(*) FROM election_voters WHERE election_id = e.id AND has_voted = TRUE) as votes_cast
        FROM elections e
        ORDER BY e.created_at DESC
    """)
    elections = cursor.fetchall()

    # Get all approved voters with election titles
    cursor.execute("""
        SELECT a.*, e.title
        FROM approved_voters a
        LEFT JOIN elections e ON a.election_id = e.id
        ORDER BY a.id DESC
    """)
    approved_voters = cursor.fetchall()

    # Get total stats
    cursor.execute("SELECT COUNT(*) FROM elections")
    total_elections = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM approved_voters")
    total_approved = cursor.fetchone()[0]

    # Get all candidates with election titles
    cursor.execute("""
        SELECT c.*, e.title
        FROM election_candidates c
        LEFT JOIN elections e ON c.election_id = e.id
        ORDER BY c.id DESC
    """)
    candidates = cursor.fetchall()

    cursor.close()
    # db.close() handled by teardown

    anomaly_status = security.detect_anomalies()
    alerts         = security.get_alerts()

    return render_template("admin_dashboard.html",
        elections       = elections,
        approved_voters = approved_voters,
        candidates      = candidates,
        total_elections = total_elections,
        total_approved  = total_approved,
        anomaly_status  = anomaly_status,
        alerts          = alerts
    )

# ─────────────────────────────────────────
# CREATE ELECTION
# ─────────────────────────────────────────
@app.route("/admin/create-election", methods=["POST"])
def create_election():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    title       = request.form["title"]
    description = request.form["description"]
    start_time  = request.form["start_time"]
    end_time    = request.form["end_time"]

    try:
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute("""
            INSERT INTO elections
            (title, description, start_time, end_time)
            VALUES (%s, %s, %s, %s)
        """, (title, description, start_time, end_time))
        db.commit()
        cursor.close()
        # db.close() handled by teardown
        flash(f"Election '{title}' created!", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/edit-election/<int:election_id>", methods=["GET", "POST"])
def edit_election(election_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    cursor = db.cursor(buffered=True)

    if request.method == "POST":
        title       = request.form["title"]
        description = request.form["description"]
        start_time  = request.form["start_time"]
        end_time    = request.form["end_time"]

        try:
            cursor.execute("""
                UPDATE elections
                SET title = %s, description = %s, start_time = %s, end_time = %s
                WHERE id = %s
            """, (title, description, start_time, end_time, election_id))
            db.commit()
            flash("Election updated successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            flash(f"Error: {e}", "error")

    # GET request: load election data
    cursor.execute("SELECT * FROM elections WHERE id = %s", (election_id,))
    election = cursor.fetchone()
    cursor.close()

    if not election:
        flash("Election not found!", "error")
        return redirect(url_for("admin_dashboard"))

    # Convert datetime objects to string format required by datetime-local input
    election_list = list(election)
    if election_list[3]: # start_time
        election_list[3] = election_list[3].strftime('%Y-%m-%dT%H:%M')
    if election_list[4]: # end_time
        election_list[4] = election_list[4].strftime('%Y-%m-%dT%H:%M')

    return render_template("edit_election.html", election=election_list)

# ─────────────────────────────────────────
# TOGGLE ELECTION
# ─────────────────────────────────────────
@app.route("/admin/toggle-election/<int:election_id>")
def toggle_election(election_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute(
        "SELECT is_active FROM elections WHERE id = %s",
        (election_id,)
    )
    current = cursor.fetchone()[0]

    cursor.execute(
        "UPDATE elections SET is_active = %s WHERE id = %s",
        (not current, election_id)
    )
    db.commit()
    cursor.close()
    # db.close() handled by teardown

    status = "started" if not current else "stopped"
    flash(f"Election {status}!", "success")
    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# RELEASE / HIDE RESULTS
# ─────────────────────────────────────────
@app.route("/admin/toggle-results/<int:election_id>")
def toggle_results(election_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute(
        "SELECT results_released FROM elections WHERE id = %s",
        (election_id,)
    )
    current = cursor.fetchone()[0]

    cursor.execute(
        "UPDATE elections SET results_released = %s WHERE id = %s",
        (not current, election_id)
    )
    db.commit()
    cursor.close()

    status = "released to voters" if not current else "hidden from voters"
    flash(f"Results {status}!", "success")
    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# ADD CANDIDATE TO ELECTION
# ─────────────────────────────────────────
@app.route("/admin/add-candidate", methods=["POST"])
def add_candidate():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    election_id = request.form["election_id"]
    name        = request.form["name"]
    party       = request.form["party"]

    try:
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute("""
            INSERT INTO election_candidates
            (election_id, name, party)
            VALUES (%s, %s, %s)
        """, (election_id, name, party))
        db.commit()
        cursor.close()
        # db.close() handled by teardown
        flash(f"Candidate {name} added!", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# DELETE CANDIDATE
# ─────────────────────────────────────────
@app.route("/admin/delete-candidate/<int:candidate_id>")
def delete_candidate(candidate_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    try:
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute(
            "DELETE FROM election_candidates WHERE id = %s",
            (candidate_id,)
        )
        db.commit()
        cursor.close()
        flash("Candidate removed successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# ADD APPROVED VOTER
# ─────────────────────────────────────────
@app.route("/admin/add-approved-voter", methods=["POST"])
def add_approved_voter():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    election_id   = request.form["election_id"]
    full_name     = request.form["full_name"]
    voter_id      = request.form["voter_id"]
    email         = request.form["email"]
    aadhar_number = request.form["aadhar_number"]
    phone         = request.form["phone"]
    dob           = request.form["date_of_birth"]
    address       = request.form.get("address", "")

    try:
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute("""
            INSERT INTO approved_voters
            (election_id, full_name, voter_id, email, aadhar_number,
             phone, date_of_birth, address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (election_id, full_name, voter_id, email,
              aadhar_number, phone, dob, address))
        db.commit()
        cursor.close()
        # db.close() handled by teardown
        flash(f"Voter {full_name} added to approved list!", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# BULK UPLOAD APPROVED VOTERS (CSV)
# ─────────────────────────────────────────
@app.route("/admin/bulk-upload-voters", methods=["POST"])
def bulk_upload_voters():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    election_id = request.form.get("election_id")
    if not election_id:
        flash("Please select an election!", "error")
        return redirect(url_for("admin_dashboard"))

    if "csv_file" not in request.files:
        flash("No file selected!", "error")
        return redirect(url_for("admin_dashboard"))

    file = request.files["csv_file"]

    if file.filename == "":
        flash("No file selected!", "error")
        return redirect(url_for("admin_dashboard"))

    if not file.filename.endswith(".csv"):
        flash("Only .csv files are allowed!", "error")
        return redirect(url_for("admin_dashboard"))

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        reader = csv.DictReader(stream)

        db = get_db()
        cursor = db.cursor(buffered=True)

        added = 0
        skipped = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                full_name     = row.get("full_name", "").strip()
                voter_id      = row.get("voter_id", "").strip()
                email         = row.get("email", "").strip()
                aadhar_number = row.get("aadhar_number", "").strip()
                phone         = row.get("phone", "").strip()
                dob           = row.get("date_of_birth", "").strip()
                address       = row.get("address", "").strip()

                if not full_name or not voter_id or not email:
                    errors.append(f"Row {row_num}: Missing required fields")
                    skipped += 1
                    continue

                cursor.execute("""
                    INSERT INTO approved_voters
                    (election_id, full_name, voter_id, email, aadhar_number,
                     phone, date_of_birth, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (election_id, full_name, voter_id, email,
                      aadhar_number, phone, dob if dob else None, address))
                added += 1

            except mysql.connector.IntegrityError:
                skipped += 1
                errors.append(f"Row {row_num}: Duplicate voter_id/email/aadhar")
            except Exception as e:
                skipped += 1
                errors.append(f"Row {row_num}: {str(e)}")

        db.commit()
        cursor.close()

        msg = f"✅ {added} voters added successfully!"
        if skipped > 0:
            msg += f" ⚠️ {skipped} skipped."
        flash(msg, "success")

        if errors:
            for err in errors[:5]:
                flash(err, "error")
            if len(errors) > 5:
                flash(f"...and {len(errors) - 5} more errors", "error")

    except Exception as e:
        flash(f"CSV Upload Error: {str(e)}", "error")

    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# DOWNLOAD SAMPLE CSV TEMPLATE
# ─────────────────────────────────────────
@app.route("/admin/sample-csv")
def download_sample_csv():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["full_name", "voter_id", "email", "aadhar_number", "phone", "date_of_birth", "address"])
    writer.writerow(["Rahul Kumar", "VOTER001", "rahul@college.edu", "123456789012", "9876543210", "2002-05-15", "Hostel Block A"])
    writer.writerow(["Priya Sharma", "VOTER002", "priya@college.edu", "234567890123", "9876543211", "2003-01-20", "Hostel Block B"])
    writer.writerow(["Amit Singh", "VOTER003", "amit@college.edu", "345678901234", "9876543212", "2002-11-10", "Day Scholar"])

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_voters.csv"}
    )

# ─────────────────────────────────────────
# DELETE APPROVED VOTER
# ─────────────────────────────────────────
@app.route("/admin/delete-approved-voter/<int:voter_id>")
def delete_approved_voter(voter_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    try:
        db = get_db()
        cursor = db.cursor(buffered=True)
        cursor.execute(
            "DELETE FROM approved_voters WHERE id = %s",
            (voter_id,)
        )
        db.commit()
        cursor.close()
        # db.close() handled by teardown
        flash("Voter removed from approved list!", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for("admin_dashboard"))

# ─────────────────────────────────────────
# ADMIN LOGOUT
# ─────────────────────────────────────────
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Admin logged out!", "success")
    return redirect(url_for("index"))

# ─────────────────────────────────────────
# AUTO CHECK ELECTION TIMER
# ─────────────────────────────────────────
@app.route("/api/check-elections")
def check_elections():
    """Auto stop elections when time expires"""
    db = get_db()
    cursor = db.cursor(buffered=True)

    cursor.execute("""
        UPDATE elections
        SET is_active = FALSE
        WHERE is_active = TRUE
        AND end_time IS NOT NULL
        AND end_time < NOW()
    """)
    db.commit()
    cursor.close()
    # db.close() handled by teardown

    return jsonify({"status": "checked"})

# ─────────────────────────────────────────
# RUN APP
# ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    #app.run(host="0.0.0.0", port=port, debug=True)
    socketio.run(app, port=5001, debug=True)
