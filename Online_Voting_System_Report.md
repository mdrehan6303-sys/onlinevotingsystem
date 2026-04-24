# Online Voting System

A Real-Time / Field-Based Research Project Report
Submitted to
Jawaharlal Nehru Technological University, Hyderabad
By

**[Student Name 1]**         ([Roll Number 1])
**[Student Name 2]**         ([Roll Number 2])
**[Student Name 3]**         ([Roll Number 3])

Under the Guidance of
**[Guide's Name]**

DEPARTMENT OF CSE
[College Name]
(An Autonomous Institution, NAAC Accredited and Affiliated to JNTUH, Hyderabad)

---

## CERTIFICATE

This is to certify that the Real-Time/Field-Based Research Project report entitled:
**“Online Voting System”** is a bonafide record of the work carried out by [Student Names] submitted to the Department of CSE, [College Name], affiliated to Jawaharlal Nehru Technological University, Hyderabad, in partial fulfillment of the requirements for the award of the degree, during the academic year 2025–2026.

Internal Guide                                     Head of the Department
**[Guide's Name]**                                 **[HOD's Name]**

Project Coordinator
**[Coordinator's Name]**

---

## DECLARATION

We hereby declare that the Real Time / Field-Based Research Project report entitled **“Online Voting System”** is an original work done and submitted to CSE Department, [College Name], affiliated to Jawaharlal Nehru Technological University, Hyderabad and it is a record of bonafide project work carried out by us under the guidance of [Guide's Name].

We further declare that the work reported in this project has not been submitted, either in part or in full, for the award of any other degree or diploma in this Institute or any other Institute or University.

Signature of the Students:
- [Student 1]
- [Student 2]
- [Student 3]

Date:
Place:

---

## ACKNOWLEDGEMENT

We are thankful and fortunate enough to get constant encouragement, support, and guidance from all Teaching staff of CSE Department who helped us in successfully completing this project work.

We thank our Project Coordinator and Project Review Committee members for their valuable guidance and support which helped us to complete the project work successfully.

We respect and thank our internal guide **[Guide's Name]** for giving us all the support and guidance, which made us complete the project duly.

We thank our Professor and Head of the Department **[HOD's Name]**, for giving us all the support and guidance which made us to complete the Real Time / Field Based Research Project duly.

Finally, we thank all those helpful to us in this regard.

---

## ABSTRACT

Elections play a crucial role in modern democratic societies. However, traditional physical voting methodologies face several challenges, including logistical complexities, long wait times, manual counting errors, and susceptibility to tampering. Despite innovations in electronic voting machines (EVMs), limitations such as lack of remote accessibility and centralized points of failure persist. This project presents a highly secure, web-based Online Voting System that bridges these gaps by integrating advanced cryptographic mechanisms, Multi-Factor Authentication (MFA), and a decentralized-inspired Blockchain ledger.

The system features dedicated interfaces for both Voters and Administrators. The Administrator dashboard provides centralized control, enabling the management of candidates, strict scheduling of active election windows, and the secure withholding of live results until an election has concluded. The Voter interface guarantees a seamless, accessible voting experience protected by robust security measures. Identity verification is securely managed through real-time Email OTP (One-Time Password) integrated directly into the registration flow. Once verified, cryptographic hashes encapsulate the voter’s identity and their cast vote, inserting it as an immutable block into the system's Blockchain ledger. 

Developed with a robust backend using Python and Flask, paired with MySQL for structured relational data storage, and integrated with Socket.IO for real-time live result broadcasts, the system achieves a highly scalable, real-time architecture. The outcome is a scalable software solution that demonstrates the potential of digital ledger technologies in establishing tamper-proof, transparent, and significantly more accessible administrative democratic processes.

---

# CHAPTER 1: INTRODUCTION

## 1.1 INTRODUCTION
In the current era of extreme digital transformation, virtually every sector of administrative operations has migrated to secure internet-based platforms. However, the mechanism of voting remains heavily reliant on physical polling stations and standalone Electronic Voting Machines (EVMs). While EVMs represent an improvement over paper ballots, they require voters to be physically present and remain vulnerable to both centralized tampering and logistical bottlenecks. 

The security and integrity of a voting process are absolute prerequisites. To shift elections to the internet, a system must guarantee the anonymity of the voter, the verifiable immutability of the vote, and absolute restriction against duplicate voting. This project focuses on utilizing modern cryptographic standards and a custom blockchain architecture to function as a primary secure voting mechanism that assists authoritative organizations in holding verifiable elections.

This project introduces a comprehensive, cloud-ready web platform logically divided into an Admin Portal and a Voter Portal. Voters can independently register online, undergo robust OTP verification against an approved registry, and cast their vote securely. The backend system encapsulates these votes into cryptographically locked blocks, linked together to form a chain where altering any historical block would inherently invalidate the entire chain.

## 1.2 LITERATURE SURVEY
The integration of blockchain and advanced cryptography into voting has been an active area of research in academic and governmental software engineering. 

Early online voting systems heavily relied on traditional centralized databases, where a single compromised database administrator could potentially manipulate entire vote counts without leaving a trace. These systems also suffered from identity-spoofing attacks due to weak single-factor authentication.

Recent advancements in cybersecurity paradigms have demonstrated that utilizing distributed ledger concepts (Blockchain) can drastically improve the security of centralized systems. According to various studies on E-Voting Systems, the utilization of hashing algorithms such as SHA-256 for data encapsulation significantly enhances the immutability of vote records. 

Identifying the limitations of existing standalone election systems, this project implements a highly responsive, real-time application that not only verifies users through email-based multi-factor authentication (OTP) but also securely stores the transactional logic of voting in an unchangeable blockchain. 

## 1.3 PROBLEM STATEMENT
Traditional democratic processes and modern corporate governance require frequent, secure elections. However, the current standard methodologies entail massive logistical overhead, restrict participation from remote individuals, and obscure the vote-tallying process from immediate public verification. 

There is a critical need for an automated, real-time system that securely bridges modern web accessibility with uncompromising data integrity. Existing E-voting applications either lack the cryptographic integrity required for large-scale trust or present overwhelmingly complex enterprise infrastructures. 

The problem is to develop a highly accessible, web-based voting system that can seamlessly verify user identities, execute cryptographic vote casting across a ledger, securely gate election results based on administrative timeframes, and intelligently manage live statistics without requiring constant manual oversight.

## 1.4 PROJECT OBJECTIVES
The main objective of this project is to develop an industry-ready digital voting platform utilizing modern cyber-security protocols to facilitate real-time, tamper-proof voting. 

Specific objectives include:
1. To develop an intuitive and responsive front-end dashboard for both voters and administrators using modern web technologies (HTML, CSS).
2. To build a robust RESTful backend routing architecture using Python and Flask.
3. To establish a secure relational database schema using MySQL to store voter registries, election schedules, and core application data.
4. To implement a functional Blockchain layer using cryptographic hashes (`SHA-256`) that verifies and securely encrypts vote data into a chain of transaction blocks.
5. To create a secure OTP-based identity verification system combined with bcrypt-secured password hashing to prevent identity spoofing and duplicate voting.
6. To deploy real-time bidirectional communication via WebSockets (`Flask-SocketIO`) to broadcast dynamic election results once authorized by the admin.

## 1.5 SOFTWARE & HARDWARE SPECIFICATIONS

### 1.5.A SOFTWARE REQUIREMENTS
The following software tools and technologies are used for the development and deployment of the Online Voting System:

1. **Operating System:** Windows / Linux / macOS
2. **Programming Languages:** Python 3.9+, JavaScript, HTML5, CSS3
3. **Backend Technologies:**
   - Flask (Python Web Framework)
   - Flask-SocketIO (Real-time WebSockets)
   - Flask-Bcrypt (Cryptographic Hashing)
4. **Database:** MySQL Server
5. **Database Connector:** mysql-connector-python
6. **Auxiliary Libraries:** 
   - `qrcode` (For receipt generation)
   - `eventlet` (Asynchronous WSGI networking)
7. **Development Tools / IDEs:** Visual Studio Code / PyCharm

### 1.5.B HARDWARE REQUIREMENTS
The following hardware components are required:
1. **Processor:** Intel i5 / AMD Ryzen 5 or higher
2. **Memory (RAM):** Minimum 8 GB
3. **Storage:** Minimum 20 GB free disk space
4. **Network:** Active internet connection (for SMTP OTP services and Socket connections)

---

# CHAPTER 2: DESIGN AND METHODOLOGY

## 2.1 SYSTEM ARCHITECTURE
The system architecture of the Online Voting System is designed utilizing a Client–Server application model based on the MVC (Model–View–Controller) design pattern, augmented by an additional Blockchain Integration Layer. 

**1. Presentation Tier (Frontend)**
Developed utilizing HTML, CSS, and interactive JavaScript. The system includes discrete, role-based dashboards for voters (Registration, Login, Voting Booth, Receipts) and administrators (Election Creation, Candidate Assignment, Result Release). User interfaces communicate with backend components asynchronously to prevent latency.

**2. Application Logic Tier (Backend REST & Controllers)**
The operational backbone of the application runs entirely on Python's Flask framework. Requests are routed and governed through rigorous session checks.
- **Security & OTP Modules:** Independent python modules (`security.py`, `otp_service.py`) abstract email SMTP transfers and `bcrypt` password verifications away from the main routes.
- **Smart Contract Validation:** Simulates logic constraints—such as time window expiration and duplicate vote prevention—restricting any voting block from executing if rules are violated.

**3. Blockchain Management Layer**
When a voter successfully submits a vote, their identity is hashed and paired with the candidate ID. The `blockchain.py` module computes the combined structural hash of this data alongside the `previous_block_hash`. By validating previous and current hashes sequentially, the system can instantly alert administrators to database tampering.

**4. Data Access Tier (Database)**
Utilizes MySQL to permanently store relation data (`elections`, `approved_voters`, `election_candidates`). The blockchain is mirrored into the relational `election_blockchain_votes` table dynamically from the live chain.

## 2.2 DATA FLOW DIAGRAM (DFD)

**Level 0: Context Diagram**
At the highest level, the voting system manages data across three entities: The Voter, The Administrator, and the Core Blockchain Database.

1. **Voter Entity:**
   - *Inputs:* Identity credentials (Aadhar, Email, Phone), OTP input, and Vote Selection.
   - *Outputs:* Verification Status, Secure E-voting dashboard, QR Code confirmation receipt.
2. **Administrator Entity:**
   - *Inputs:* Election start/end dates, Candidate details, Authorization toggles to release results.
   - *Outputs:* Administrative Dashboard, Chain-validity checks, Live analytic turnout data.
3. **System Database / Ledger:**
   - Maintains transactional records. The Flask application queries logic from the Relational database and permanently records validated transactions onto the immutable Blockchain.

## 2.3 TECHNOLOGY DESCRIPTION

1. **Python & Flask Framework**
   Flask is a lightweight WSGI web application framework. It provides the core routing backbone, maintaining session-based contexts and integrating seamlessly with HTML rendering endpoints via Jinja2 templating.

2. **MySQL Database Engine**
   Used to build structured, relational sets for highly associated data. It maintains strict primary and foreign key structures, ensuring relationships between Voters and distinct Elections are strictly enforced and queryable.

3. **Cryptographic Blockchain Integration**
   Unlike simple databases, votes are committed to an internal class-based Blockchain instance. Each block's `current_hash` is algorithmically generated based heavily on the `previous_hash`. If a database cell is retroactively modified directly through SQL, the localized chain iteration verifies and automatically flags the chain status as "Invalid."

4. **WebSockets (Flask-SocketIO)**
   Traditional HTTP requires clients to "poll" servers for updates. SocketIO is integrated to allow the server to "push" updates dynamically. The moment a vote enters the ledger, listening client dashboards instantly reflect live statistics, crucial for post-election transparency.

---

# CHAPTER 3: IMPLEMENTATION

## 3.1 SYSTEM IMPLEMENTATION
The system utilizes a fully modular implementation separating concerns into dedicated python service files. 

**Database Initializations:** 
A highly optimized database pooling strategy is implemented in `app_db.py`. This ensures high-throughput database operations do not open excessive concurrent connections, guaranteeing system stability under heavy voter load.

**OTP Generation and Security:** 
To prevent automated accounts, an initial gatecheck requires voters to match an institutional pre-approved list. If a match is found, the `OTPService` generates random 6-digit numeric sequences securely transferred via Python’s `smtplib`. Temporary registers are stored strictly in session memory until validated.

**Vote Casting Logic:** 
To submit a vote, users log in using hashed credentials. A secondary verification confirms that `has_voted` evaluates to FALSE. Upon casting, `blockchain.py` invokes `add_vote()` wrapping the credentials inside a SHA256 hashed node. The backend actively modifies candidate vote-counts asynchronously while providing a downloadable QR code-based receipt for the voter.

## 3.2 CODE SNIPPETS

**Blockchain Engine Core (`blockchain.py`)**
```python
def create_block(self, voter_hash, candidate_id):
    block = Block(
        index=len(self.chain) + 1,
        voter_hash=voter_hash,
        candidate_id=candidate_id,
        previous_hash=self.chain[-1].current_hash
    )
    self.chain.append(block)
    return block
```

**Security Hashing Module (`security.py`)**
```python
def hash_voter_identity(self, voter_id):
    """Creates a deterministic hash of the voter ID ensuring anonymity"""
    salt = self.app.secret_key.encode('utf-8')
    data = str(voter_id).encode('utf-8')
    return hashlib.pbkdf2_hmac('sha256', data, salt, 100000).hex()
```

**Admin Gated Route Architecture (`app.py`)**
```python
@app.route("/election/<int:election_id>/results")
def results(election_id):
    # Check if results are released — only admin can bypass
    is_admin = "admin" in session
    results_released = election[7]
    if not results_released and not is_admin:
        flash("Results have not been released yet by the admin.", "error")
        return redirect(url_for("election_home", election_id=election_id))
    # Render final tally
```

## 3.3 RESULTS
The developed system operates successfully as a secure, full-stack cryptographic voting application. 

**Voter Portal Flow:**
The system effectively isolates secure voting parameters. Voters verify identity, successfully interact with localized ballot interfaces, and receive timestamped mathematical QR code receipts acting as permanent proof of democratic participation.

**Admin Dashboard Insights:**
Authorized personnel successfully navigate administrative portals authorizing elections. Crucially, the system correctly gates public access to voting results until the administrator manually publishes them.

**Data Consistency & Blockchain Verification:**
The blockchain functionality demonstrably blocks repeated voting instances. By storing the index, candidate hash, previous hash, and current block validation hash in MySQL, the system successfully bridges relational query speeds with Blockchain-grade data immutability.

---

# CHAPTER 4: CONCLUSION AND FUTURE SCOPE

## 4.1 CONCLUSION
The Online Voting System successfully demonstrates that internet-based voting can be constructed safely by replacing generic database writes with cryptographic blockchain mechanics and multi-factor authentication loops. 

By implementing Python and Flask on the backend, the application maintained scalable logic separation. The deployment of MySQL allowed for complex relationships managing concurrent distinct election events. Importantly, the implementation of a real-time mathematical ledger, email OTP verification, and strict administrative gating processes proved that democratic accessibility and security are not mutually exclusive. This framework provides an extremely viable alternative to the costly and complicated physical voting standard.

## 4.2 FUTURE SCOPE
The current implementation utilizes a highly localized blockchain instance mirrored onto a relational database. Future improvements can involve distributing the validation nodes (Decentralization) using peer-to-peer (P2P) networking across multiple servers, making database modifications fundamentally impossible without network consensus.

Further additions include incorporating biometric scanning functionality directly matching government identity servers (such as live visual face recognition) or integrating the system into mobile-native applications (Android/iOS) using frameworks like React Native to enhance user convenience. 

## 4.3 REFERENCES
1. Flask Web Framework Documentation. Available: https://flask.palletsprojects.com/ 
2. Blockchain Structural Theory (Satoshi Nakamoto). "Bitcoin: A Peer-to-Peer Electronic Cash System."
3. MySQL Database Design and Implementation Documentation.
4. Python Cryptographic Authority (hashlib/bcrypt).
5. WebSockets Interface reference (Flask-SocketIO).

## 4.4 APPENDIX (SOURCE CODE EXCERPTS)

*(Excerpts of core configuration files)*

**app_db.py (Optimized Connection Pooling)**
```python
from mysql.connector import pooling
def init_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,
            host='localhost',
            user='root',
            password='',
            database='secure_voting'
        )
```

**requirements.txt**
```text
flask
mysql-connector-python
flask-socketio
flask-bcrypt
qrcode
```
