"""
Lead Scoring Model Trainer
Run this once to generate the saved model file: lead_model.pkl
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import json

# ── Synthetic Training Data ───────────────────────────────────────────────────
np.random.seed(42)
n = 500

def generate_leads(n):
    data = []
    for _ in range(n):
        job_seniority   = np.random.choice([0, 1, 2, 3], p=[0.3, 0.3, 0.25, 0.15])
        # 0=individual, 1=manager, 2=director, 3=c-suite/vp

        company_size    = np.random.choice([0, 1, 2, 3], p=[0.3, 0.3, 0.25, 0.15])
        # 0=1-10, 1=11-50, 2=51-200, 3=200+

        budget_flag     = np.random.choice([0, 1], p=[0.5, 0.5])
        # 0=no budget mentioned, 1=budget mentioned

        timeline        = np.random.choice([0, 1, 2], p=[0.4, 0.35, 0.25])
        # 0=no timeline, 1=3-6 months, 2=immediate (<3 months)

        pain_points     = np.random.randint(0, 5)
        # number of pain points described (0-4)

        industry_fit    = np.random.choice([0, 1], p=[0.4, 0.6])
        # 0=low fit industry, 1=high fit industry

        # Weighted scoring logic for labeling
        score = (
            job_seniority   * 20 +
            company_size    * 15 +
            budget_flag     * 25 +
            timeline        * 15 +
            pain_points     *  5 +
            industry_fit    * 10
        )
        # Max possible: 60+45+25+30+20+10 = 190 — normalise to 100
        score_norm = round((score / 190) * 100)

        if score_norm >= 60:
            tier = 2   # hot
        elif score_norm >= 35:
            tier = 1   # warm
        else:
            tier = 0   # cold

        data.append([
            job_seniority, company_size, budget_flag,
            timeline, pain_points, industry_fit,
            score_norm, tier
        ])

    return pd.DataFrame(data, columns=[
        "job_seniority", "company_size", "budget_flag",
        "timeline", "pain_points", "industry_fit",
        "score", "tier"
    ])

df = generate_leads(n)

# ── Train Model ───────────────────────────────────────────────────────────────
features = ["job_seniority", "company_size", "budget_flag",
            "timeline", "pain_points", "industry_fit"]

X = df[features]   # already a DataFrame — sklearn will store feature names
y = df["tier"]

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X, y)      # feature names are now bound to the model

# ── Save Model ────────────────────────────────────────────────────────────────
joblib.dump(clf, "lead_model.pkl")
print("✅ Model trained and saved as lead_model.pkl")
print(f"   Training samples : {n}")
print(f"   Features         : {features}")
print(f"   Classes          : cold(0), warm(1), hot(2)")
