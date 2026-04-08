# otp_service.py
import random
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

class OTPService:

    def __init__(self):
        self.gmail_address  = "mdrehan6303@gmail.com"
        self.gmail_password = "wfwqyafrdmjhybex"
        self.otp_storage = {}

    def generate_otp(self):
        return str(random.randint(100000, 999999))

    def send_otp_email(self, receiver_email, otp, voter_name):
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = "SecureVote Your OTP Verification Code"
            message["From"]    = self.gmail_address
            message["To"]      = receiver_email

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;
                         background-color: #f0f2f5;
                         padding: 20px;">
                <div style="max-width: 500px;
                            margin: 0 auto;
                            background: white;
                            border-radius: 15px;
                            padding: 30px;">
                    <h2 style="color: #1a237e; text-align: center;">
                        SecureVote
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
                    <p>This OTP is valid for 5 minutes only.</p>
                    <p>Do not share this OTP with anyone.</p>
                    <p style="color: #1a237e; text-align: center;">
                        <strong>SecureVote Blockchain Based Voting System</strong><br>
                        CVR College of Engineering | Dept. of CSE(DS)
                    </p>
                </div>
            </body>
            </html>
            """

            part = MIMEText(html_content, "html")
            message.attach(part)

            # Method 1 — SSL with unverified context
            try:
                print("Trying SSL connection...")
                context = ssl._create_unverified_context()
                with smtplib.SMTP_SSL(
                    "smtp.gmail.com", 465, context=context
                ) as server:
                    server.login(
                        self.gmail_address,
                        self.gmail_password
                    )
                    server.sendmail(
                        self.gmail_address,
                        receiver_email,
                        message.as_string()
                    )
                print(f"OTP sent via SSL to {receiver_email}")
                return True

            except Exception as ssl_error:
                print(f"SSL failed: {ssl_error}")

                # Method 2 — TLS with unverified context
                try:
                    print("Trying TLS connection...")
                    context = ssl._create_unverified_context()
                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.ehlo()
                        server.starttls(context=context)
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
                    print(f"OTP sent via TLS to {receiver_email}")
                    return True

                except Exception as tls_error:
                    print(f"TLS failed: {tls_error}")
                    raise tls_error

        except Exception as e:
            print(f"Error sending OTP email: {e}")
            return False

    def store_otp(self, email, otp):
        expiry_time = datetime.now() + timedelta(minutes=5)
        self.otp_storage[email] = {
            "otp":    otp,
            "expiry": expiry_time
        }
        print(f"OTP stored for {email}")
        print(f"OTP is: {otp}")

    def verify_otp(self, email, entered_otp):
        if email not in self.otp_storage:
            return "notfound"

        stored = self.otp_storage[email]

        if datetime.now() > stored["expiry"]:
            del self.otp_storage[email]
            return "expired"

        if stored["otp"] == entered_otp:
            del self.otp_storage[email]
            return "valid"

        return "invalid"

    def generate_and_send(self, email, voter_name):
        otp = self.generate_otp()
        self.store_otp(email, otp)
        return self.send_otp_email(email, otp, voter_name)