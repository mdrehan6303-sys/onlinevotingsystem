"""
NovaVote — ML Evaluation: Confusion Matrix for Isolation Forest
Evaluates the anomaly detection model from security.py.

In production, the model trains on 110 synthetic baselines PLUS real DB logs.
This script simulates that full pipeline with realistic voting data.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (confusion_matrix, classification_report,
                             accuracy_score, f1_score, precision_score, recall_score)
import os

np.random.seed(42)

# ═══════════════════════════════════════════
# 1. TRAINING DATA
# Base synthetic data (from security.py) + simulated real DB logs
# In production, _load_training_data() merges these automatically
# ═══════════════════════════════════════════
training_data = []

# --- Synthetic baselines (exact copy from security.py lines 31-34) ---
for _ in range(40): training_data.append([np.random.randint(9, 11), np.random.randint(0, 59), 1])
for _ in range(10): training_data.append([np.random.randint(12, 13), np.random.randint(0, 59), 1])
for _ in range(25): training_data.append([np.random.randint(14, 16), np.random.randint(0, 59), 1])
for _ in range(35): training_data.append([np.random.randint(18, 20), np.random.randint(0, 59), 1])

# --- Simulated real DB logs (ai_voting_logs table) ---
# In production: cursor.execute("SELECT hour, minute, voter_hash_segment FROM ai_voting_logs")
# hash(voter_id) % 1000 produces varied values in real usage
for _ in range(50): training_data.append([np.random.randint(9, 11), np.random.randint(0, 59), np.random.randint(1, 200)])
for _ in range(30): training_data.append([np.random.randint(14, 17), np.random.randint(0, 59), np.random.randint(1, 200)])
for _ in range(40): training_data.append([np.random.randint(18, 20), np.random.randint(0, 59), np.random.randint(1, 200)])

training_data = np.array(training_data)
print(f"Training: {len(training_data)} samples (110 synthetic + 120 simulated DB logs)")

# ═══════════════════════════════════════════
# 2. TRAIN — same parameters as security.py
# ═══════════════════════════════════════════
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(training_data)

# ═══════════════════════════════════════════
# 3. TEST DATA — labeled ground truth
# ═══════════════════════════════════════════

# NORMAL: votes during standard hours (9-20), reasonable hash values
normal_test = []
for _ in range(30): normal_test.append([np.random.randint(9, 11), np.random.randint(0, 59), np.random.randint(1, 150)])
for _ in range(10): normal_test.append([np.random.randint(12, 14), np.random.randint(0, 59), np.random.randint(1, 150)])
for _ in range(20): normal_test.append([np.random.randint(14, 17), np.random.randint(0, 59), np.random.randint(1, 150)])
for _ in range(20): normal_test.append([np.random.randint(18, 20), np.random.randint(0, 59), np.random.randint(1, 150)])

# ANOMALOUS: votes at unusual hours AND/OR extreme hash values
anomalous_test = []
# Midnight voting (0-4 AM) — highly suspicious
for _ in range(8): anomalous_test.append([np.random.randint(0, 4), np.random.randint(0, 59), np.random.randint(500, 999)])
# Late night (22-24) — suspicious
for _ in range(7): anomalous_test.append([np.random.randint(22, 24), np.random.randint(0, 59), np.random.randint(500, 999)])
# Early dawn (5-7 AM) with high hash
for _ in range(5): anomalous_test.append([np.random.randint(5, 7), np.random.randint(0, 59), np.random.randint(600, 999)])
# Bot-like: extreme hash values even during normal hours
for _ in range(5): anomalous_test.append([np.random.randint(9, 20), np.random.randint(0, 59), np.random.randint(800, 999)])

X_normal = np.array(normal_test)
X_anomalous = np.array(anomalous_test)
X_test = np.vstack([X_normal, X_anomalous])
y_true = np.array([1] * len(X_normal) + [-1] * len(X_anomalous))

print(f"Test:     {len(X_test)} samples ({len(X_normal)} normal + {len(X_anomalous)} anomalous)")

# ═══════════════════════════════════════════
# 4. PREDICT & EVALUATE
# ═══════════════════════════════════════════
y_pred = model.predict(X_test)

cm = confusion_matrix(y_true, y_pred, labels=[1, -1])
tn, fp, fn, tp = cm.ravel()

acc    = accuracy_score(y_true, y_pred)
prec_n = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
rec_n  = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
f1_n   = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
prec_a = precision_score(y_true, y_pred, pos_label=-1, zero_division=0)
rec_a  = recall_score(y_true, y_pred, pos_label=-1, zero_division=0)
f1_a   = f1_score(y_true, y_pred, pos_label=-1, zero_division=0)

print(f"\n{'═'*55}")
print(f"  RESULTS — Isolation Forest (contamination=0.1)")
print(f"{'═'*55}")
print(f"  TN={tn}  FP={fp}  FN={fn}  TP={tp}")
print(f"  Accuracy:          {acc*100:.1f}%")
print(f"  Anomaly Precision: {prec_a*100:.1f}%")
print(f"  Anomaly Recall:    {rec_a*100:.1f}%")
print(f"  Anomaly F1-Score:  {f1_a:.4f}")
print(f"\n{classification_report(y_true, y_pred, labels=[1, -1], target_names=['Normal', 'Anomaly'])}")

# ═══════════════════════════════════════════
# 5. VISUALIZATION
# ═══════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(16, 7.5),
                         gridspec_kw={'width_ratios': [1.15, 0.85]})
fig.patch.set_facecolor('#0f1419')

# ── Left Panel: Confusion Matrix ──
ax = axes[0]
ax.set_facecolor('#161b22')

cmap = LinearSegmentedColormap.from_list('nova',
    ['#161b22', '#1a237e', '#283593', '#304ffe', '#448aff', '#82b1ff'])
im = ax.imshow(cm, interpolation='nearest', cmap=cmap, aspect='auto')

ax.set_title('Confusion Matrix — Isolation Forest',
             fontsize=16, fontweight='bold', color='white', pad=18)
ax.set_xlabel('Predicted Label', fontsize=12, color='#8b949e', labelpad=14)
ax.set_ylabel('Actual Label', fontsize=12, color='#8b949e', labelpad=14)

tick_labels = ['Normal\n(Inlier)', 'Anomaly\n(Outlier)']
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(tick_labels, fontsize=11.5, color='white')
ax.set_yticklabels(tick_labels, fontsize=11.5, color='white')

cell_names  = [['TN', 'FP'], ['FN', 'TP']]
cell_colors = [['#4caf50', '#ff5252'], ['#ff9800', '#4caf50']]
cell_desc   = [['Correct\nNormal', 'False\nAlarm'], ['Missed\nAnomaly', 'Caught\nAnomaly']]

for i in range(2):
    for j in range(2):
        val = cm[i, j]
        total = cm[i].sum()
        pct = val / total * 100 if total > 0 else 0
        ax.text(j, i, f'{cell_names[i][j]}\n{val}\n({pct:.0f}%)',
                ha='center', va='center', fontsize=15, fontweight='bold',
                color=cell_colors[i][j],
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#0d1117',
                          edgecolor=cell_colors[i][j], alpha=0.85, linewidth=1.5))

for spine in ax.spines.values():
    spine.set_edgecolor('#30363d')
ax.tick_params(colors='white')

cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white', fontsize=9)

# ── Right Panel: Metrics + Config ──
ax2 = axes[1]
ax2.set_facecolor('#0f1419')
ax2.axis('off')

panel = (
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "     EVALUATION METRICS\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    f"  Overall Accuracy:   {acc*100:.1f}%\n\n"
    f"  ┌──── Normal ─────────┐\n"
    f"  │ Precision:  {prec_n*100:5.1f}%   │\n"
    f"  │ Recall:     {rec_n*100:5.1f}%   │\n"
    f"  │ F1-Score:   {f1_n:.4f}  │\n"
    f"  └──────────────────────┘\n\n"
    f"  ┌──── Anomaly ────────┐\n"
    f"  │ Precision:  {prec_a*100:5.1f}%   │\n"
    f"  │ Recall:     {rec_a*100:5.1f}%   │\n"
    f"  │ F1-Score:   {f1_a:.4f}  │\n"
    f"  └──────────────────────┘\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "     MODEL CONFIG\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "  Isolation Forest\n"
    "  (scikit-learn)\n\n"
    "  contamination = 0.1\n"
    "  random_state  = 42\n\n"
    "  Features:\n"
    "   • hour (0–23)\n"
    "   • minute (0–59)\n"
    "   • voter_hash_segment\n\n"
    f"  Train: {len(training_data)} samples\n"
    f"  Test:  {len(X_normal)}N + {len(X_anomalous)}A\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
)

ax2.text(0.03, 0.97, panel, transform=ax2.transAxes,
         fontsize=10.5, fontfamily='monospace', color='#58a6ff',
         verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#161b22',
                   edgecolor='#30363d', linewidth=1.2))

fig.suptitle('NovaVote — Anomaly Detection Model Evaluation',
             fontsize=18, fontweight='bold', color='white', y=0.99)

plt.tight_layout(rect=[0, 0, 1, 0.95])

# Save
base = os.path.dirname(os.path.abspath(__file__))
for p in [os.path.join(base, 'static', 'confusion_matrix.png'),
          os.path.join(base, 'confusion_matrix_report.png')]:
    plt.savefig(p, dpi=200, bbox_inches='tight', facecolor='#0f1419', edgecolor='none')
    print(f"✅ {p}")

plt.close()
print("\nDone!")
