import os
import re

targets = ["vote", "verify_otp", "resend_otp", "voter_logout", "results"]
templates_dir = "templates"

for root, _, files in os.walk(templates_dir):
    for filename in files:
        if not filename.endswith(".html"): continue
        if filename in ["index.html", "admin_login.html", "admin_dashboard.html"]: continue

        path = os.path.join(root, filename)
        with open(path, "r") as f:
            content = f.read()

        for t in targets:
            # Match url_for('target') or url_for("target")
            # Uses negative lookbehind/lookahead to avoid replacing ones that already have election_id
            pattern_sq = r"url_for\(\s*'" + t + r"'\s*\)(?=[^}]*election_id)?"

            # Simple replace if it literally matches url_for('target')
            content = content.replace(f"url_for('{t}')", f"url_for('{t}', election_id=election_id)")
            content = content.replace(f'url_for("{t}")', f'url_for("{t}", election_id=election_id)')

        with open(path, "w") as f:
            f.write(content)

print("Replacement complete!")
