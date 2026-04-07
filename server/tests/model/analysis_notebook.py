# %% [markdown]
# # SmartMailbox Model Evaluation Analysis
# This notebook analyzes the benchmark results comparing Native Vision-Language Models 
# (Qwen3) against a two-step OCR + LLM pipeline (Tesseract + Llama).

# %%
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set visual aesthetics
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({'figure.figsize': (12, 7), 'font.size': 12})

# %% [markdown]
# ### 1. Data Loading & Preprocessing
# Connect to the SQLite DB and merge the tables to create a comprehensive DataFrame.

# %%
# Resolve DB Path dynamically
# base_dir = os.path.dirname(os.path.abspath(__file__))
# db_path = os.path.abspath(os.path.join(base_dir, "../../app/db/database.db"))
DB_PATH ="C:/Programming/studienarbeit/SmartMailbox/server/app/db/database.db"
if not os.path.exists(DB_PATH):
    print(f"Warning: Database not found at {DB_PATH}.")

con = sqlite3.connect(DB_PATH)

query = """
SELECT 
    m.name AS model_name,
    m.family AS model_family,
    tc.image_selection,
    mtr.time AS total_time,
    mtr.tesseract_time,
    mtr.llama_time,
    mtr.match_found,
    mtr.correct_recipient_ids,
    mtr.correct_best_image_id,
    (mtr.match_found = 1 AND mtr.correct_recipient_ids = 1 AND mtr.correct_best_image_id = 1) AS is_perfect_run,
    mtr.error_msg
FROM model_test_results mtr
JOIN model_tests mt ON mtr.model_test_id = mt.id
JOIN models m ON mt.model = m.id
JOIN test_cases tc ON mt.test_case_id = tc.id;
"""

df = pd.read_sql_query(query, con)
con.close()

# Extract numeric model size in billions of parameters (if applicable) for scaling laws
def extract_params(name):
    import re
    match = re.search(r':(\d+)b', name)
    if match:
        return float(match.group(1))
    return None

df['param_size_b'] = df['model_name'].apply(extract_params)

# Convert boolean columns to actual bools if they are ints
bool_cols = ['match_found', 'correct_recipient_ids', 'correct_best_image_id', 'is_perfect_run']
for col in bool_cols:
    df[col] = df[col].astype(bool)

q_hi  = df["total_time"].quantile(0.99)
outliers = df[df["total_time"] >= q_hi]
print(f"Removed {len(outliers)} outliers:")
print(outliers.to_string())
df = df[df["total_time"] < q_hi]

df.head()

# %% [markdown]
# ### 2. Overall Architecture Comparison: Native Vision vs. OCR+LLM
# Let's look at the absolute success rate grouped by model.

# %%
agg_df = df.groupby('model_name').agg(
    accuracy=('is_perfect_run', 'mean'),
    avg_time=('total_time', 'mean'),
    family=('model_family', 'first')
).reset_index()

# Sort by accuracy
agg_df = agg_df.sort_values('accuracy', ascending=False)

plt.figure(figsize=(10, 6))
ax = sns.barplot(data=agg_df, x='accuracy', y='model_name', hue='family', dodge=False)
ax.set_title("Overall Accuracy by Model (Strict Evaluation)", fontweight='bold')
ax.set_xlabel("Accuracy Rate (1.0 = 100%)")
ax.set_ylabel("")
ax.set_xlim(0, 1.05)

# Annotate percentages
for p in ax.patches:
    width = p.get_width()
    if width > 0:
        ax.text(width + 0.01, p.get_y() + p.get_height()/2., f'{width:.1%}', ha="left", va="center")

plt.tight_layout()
plt.show()

# %% [markdown]
# ### 3. Inference Time & Processing Pipeline Cost
# How much overhead does the Tesseract OCR layer add compared to a native VLM approach?

# %%
time_df = df.groupby('model_name')[['tesseract_time', 'llama_time', 'total_time']].mean().reset_index()
time_df = time_df.sort_values('total_time')

fig, ax = plt.subplots(figsize=(10, 6))

# Qwen uses total_time natively. Llama models use tesseract + llama.
# We will plot Tesseract as bottom bar, Llama as top bar.
qwen_mask = time_df['model_name'].str.contains('qwen')
llama_mask = time_df['model_name'].str.contains('llama')

# Plot Qwen Models (Single block)
ax.barh(time_df[qwen_mask]['model_name'], time_df[qwen_mask]['total_time'], color='#4C72B0', label='Native VLM Time (Qwen)')

# Plot Llama Models (Stacked)
ax.barh(time_df[llama_mask]['model_name'], time_df[llama_mask]['tesseract_time'], color='#DD8452', label='OCR Time (Tesseract)')
ax.barh(time_df[llama_mask]['model_name'], time_df[llama_mask]['llama_time'], left=time_df[llama_mask]['tesseract_time'], color='#55A868', label='LLM Time (Llama)')

ax.set_title("Average Inference Time Breakdown", fontweight='bold')
ax.set_xlabel("Time (seconds)")
ax.legend(loc='lower right')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 4. Latency Stability (Boxplots)
# Averages hide outliers. We need to ensure models behave predictably on edge devices.

# %%
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='total_time', y='model_name', hue='model_family', showfliers=True)
plt.title("Inference Time Distribution (Checking for long-tail outliers)", fontweight='bold')
plt.xlabel("Total Time (seconds)")
plt.ylabel("")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 5. Robustness to Noise (Image Quality)
# How well do different models handle bad camera captures (blurry / cut off)?

# %%
quality_df = df.groupby(['model_name', 'image_selection'])['is_perfect_run'].mean().unstack()

# Optional: order the columns logically if they follow this convention
ordered_cols = ['PERFECT', 'SLIGHTLY_BLURRED', 'VERY_BLURRED', 'CUT_OFF', 'ALL']
existing_cols = [c for c in ordered_cols if c in quality_df.columns]
quality_df = quality_df[existing_cols]

plt.figure(figsize=(10, 6))
sns.heatmap(quality_df, annot=True, fmt=".1%", cmap="RdYlGn", vmin=0, vmax=1)
plt.title("Model Robustness Heatmap: Accuracy vs. Image Quality", fontweight='bold')
plt.ylabel("")
plt.xlabel("Image Condition")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 6. Failure Mode Analysis
# When a model fails, does it hallucinate JSON (Match Found = False), extract the wrong recipient, or pick the wrong image?

# %%
def categorize_failure(row):
    if row['is_perfect_run']:
        return 'Success'
    elif not row['match_found']:
        return 'Failed: Invalid JSON / Schema'
    elif not row['correct_recipient_ids']:
        return 'Failed: Wrong Recipient'
    elif not row['correct_best_image_id']:
        return 'Failed: Wrong Best Image'
    else:
        return 'Failed: Other'

df['outcome'] = df.apply(categorize_failure, axis=1)

outcome_counts = df.groupby(['model_name', 'outcome']).size().unstack(fill_value=0)
# Convert to percentages
outcome_pct = outcome_counts.div(outcome_counts.sum(axis=1), axis=0) * 100

# Sort by Success rate
if 'Success' in outcome_pct.columns:
    outcome_pct = outcome_pct.sort_values('Success')

outcome_pct.plot(kind='barh', stacked=True, figsize=(12, 7),
                 color=['#D62728', '#E66101', '#F4A582', '#2CA02C'])

plt.title("Failure Mode Distribution per Model", fontweight='bold')
plt.xlabel("Percentage of Test Cases (%)")
plt.ylabel("")
plt.legend(title='Outcome', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xlim(0, 100)
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 7. The Pareto Frontier: Speed vs. Accuracy
# Identify the optimal models for production based on edge-device constraints.

# %%
plt.figure(figsize=(10, 6))
sns.scatterplot(data=agg_df, x='avg_time', y='accuracy', hue='family', s=150, style='family', markers=['o', 's'])

# Annotate points
for i, row in agg_df.iterrows():
    if pd.notnull(row['avg_time']) and pd.notnull(row['accuracy']):
        plt.annotate(f"{row['model_name']}\n({row['avg_time']:.1f}s, {row['accuracy']:.1%})",
                     (row['avg_time'], row['accuracy']),
                     xytext=(8, -10), textcoords='offset points', fontsize=9)

plt.title("Pareto Frontier: Speed vs. Accuracy Trade-off", fontweight='bold')
plt.xlabel("Average Inference Time (seconds) ➔ (Lower is Better)")
plt.ylabel("Accuracy ➔ (Higher is Better)")
plt.ylim(0, 1.05)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 8. Scaling Laws (Qwen Family)
# Performance returns as model parameter count increases.

# %%
qwen_df = agg_df[(agg_df['family'] == 'ModelFamily.Qwen3') | (agg_df['model_name'].astype(str).str.contains('qwen'))].copy()
qwen_df['params'] = qwen_df['model_name'].astype(str).apply(extract_params)
qwen_df = qwen_df.dropna(subset=['params']).sort_values('params')

if not qwen_df.empty:
    fig, ax1 = plt.subplots(figsize=(9, 5))
    
    ax1.plot(qwen_df['params'], qwen_df['accuracy'], marker='o', color='#2CA02C', linewidth=2, markersize=8)

    for i, row in qwen_df.iterrows():
        ax1.annotate(f"{row['accuracy']:.1%}", (row['params'], row['accuracy']),
                     xytext=(0, 10), textcoords='offset points', ha='center', fontsize=10)

    ax1.set_title("Scaling Laws: Qwen Parameter Count vs Accuracy", fontweight='bold')
    ax1.set_xlabel("Parameters (Billions) - Log Scale")
    ax1.set_ylabel("Accuracy Rate")
    ax1.set_xscale('log')
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plt.show()