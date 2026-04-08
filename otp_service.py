# otp_service.py
# Handles OTP generation, sending and verification

import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

class OTPService:
    """
    OTPService handles everything related to OTP:
    1. Generate random 6 digit OTP
    2. Send OTP to voter's email
    3. Verify if OTP is correct
    4. Check if OTP has expired
    """

    def __init__(self):
        # Your Gmail credentials
        # Replace with your actual Gmail and App Password!
        self.gmail_address  = "mdrehan6303@gmail.com"
        self.gmail_password = "azhk hxvw chep ugdm"

        # Store OTPs temporarily in memory
        # Format: {"email": {"otp": "123456", "expiry": datetime}}
        self.otp_storage = {}

    def generate_otp(self):
        """
        Generates a random 6 digit OTP
        Example: 847392
        """
        return str(random.randint(100000, 999999))

    def send_otp_email(self, receiver_email, otp, voter_name):
        """
        Sends OTP to voter's email using Gmail.

        Think of this like our system sending a letter
        to the voter with their secret code inside!
        """
        try:
            # Create email message
            message = MIMEMultipart("alternative")
            message["Subject"] = "🗳️ SecureVote — Your OTP Verification Code"
            message["From"]    = self.gmail_address
            message["To"]      = receiver_email

            # Email content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;
                         background-color: #f0f2f5;
                         padding: 20px;">

                <div style="max-width: 500px;
                            margin: 0 auto;
                            background: white;
                            border-radius: 15px;
                            padding: 30px;
                            box-shadow: 0 4px 15px rgba(0,0,0,0.1);">

                    <h2 style="color: #1a237e; text-align: center;">
                        🗳️ SecureVote
                    </h2>

                    <p>Dear <strong>{voter_name}</strong>,</p>

                    <p>Your OTP verification code is:</p>

                    <div style="background: #e8eaf6;
                                border-radius: 10px;
                                padding: 20px;
                                text-align: center;
                                margin: 20px 0;">
                        <h1 style="color: #1a237e;
                                   font-size: 2.5rem;
                                   letter-spacing: 10px;">
                            {otp}
                        </h1>
                    </div>

                    <p>⏰ This OTP is valid for <strong>5 minutes only.</strong></p>
                    <p>🔐 Do not share this OTP with anyone.</p>
                    <p>✅ Enter this code on the SecureVote website to verify.</p>

                    <hr style="margin: 20px 0;">

                    <p style="color: #999; font-size: 0.85rem;">
                        If you did not request this OTP,
                        please ignore this email.
                    </p>

                    <p style="color: #1a237e; text-align: center;">
                        <strong>SecureVote — Blockchain Based Voting System</strong><br>
                        CVR College of Engineering | Dept. of CSE(DS)
                    </p>

                </div>
            </body>
            </html>
            """

            # Attach HTML content to email
            part = MIMEText(html_content, "html")
            message.attach(part)

            # Connect to Gmail and send
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(
                   self.gmail_address,
                   self.gmail_password
                )
                server.sendmail(
                    self.gmail_address,
                    receiver_email,
                    message.as_string()
                )

            print(f"OTP sent successfully to {receiver_email}")
            return True

        except Exception as e:
            print(f"Error sending OTP email: {e}")
            return False

    def store_otp(self, email, otp):
        """
        Stores OTP with 5 minute expiry time.

        Think of it like a token that expires —
        like a movie ticket that is only valid for today!
        """
        expiry_time = datetime.now() + timedelta(minutes=5)
        self.otp_storage[email] = {
            "otp":    otp,
            "expiry": expiry_time
        }
        print(f"OTP stored for {email}, expires at {expiry_time}")

    def verify_otp(self, email, entered_otp):
        """
        Checks if the entered OTP is correct and not expired.

        Returns:
        - "valid"   → OTP is correct and not expired ✅
        - "expired" → OTP has expired ⏰
        - "invalid" → Wrong OTP entered ❌
        - "notfound"→ No OTP found for this email
        """
        if email not in self.otp_storage:
            return "notfound"

        stored = self.otp_storage[email]

        # Check if OTP has expired
        if datetime.now() > stored["expiry"]:
            del self.otp_storage[email]
            return "expired"

        # Check if OTP matches
        if stored["otp"] == entered_otp:
            del self.otp_storage[email]
            return "valid"

        return "invalid"

    def generate_and_send(self, email, voter_name):
        """
        Main function — generates OTP, stores it and sends email.
        Returns True if sent successfully, False if failed.
        """
        otp = self.generate_otp()
        self.store_otp(email, otp)
        return self.send_otp_email(email, otp, voter_name)