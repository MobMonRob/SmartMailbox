# %% [markdown]
# # SmartMailbox Model Evaluation Analysis
# This notebook analyzes the benchmark results comparing Native Vision-Language Models 
# (Qwen3.5) against a two-step OCR + LLM pipeline (Tesseract + Llama).

# %%
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set visual aesthetics
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    'figure.figsize': (12, 7), 
    'font.size': 12,
    'figure.dpi': 300,       # High resolution for inline rendering
    'savefig.dpi': 300,      # High resolution for saving (300 DPI is standard for print)
    'savefig.format': 'svg', # Scalable vector format by default (or 'svg')
    'savefig.bbox': 'tight'  # Ensures labels and legends are not cut off when saving
})

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
    if 'scout' in str(name).lower():
        return 109.0
    match = re.search(r':(\d+)b', name)
    if match:
        return float(match.group(1))
    return 0.0 # Default for edge models without 'b' in name

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

# Sort models by Family then Size, and make model_name categorical to enforce this order globally
unique_models = df[['model_name', 'model_family', 'param_size_b']].drop_duplicates()
unique_models = unique_models.sort_values(by=['model_family', 'param_size_b'])
ordered_model_names = unique_models['model_name'].tolist()
df['model_name'] = pd.Categorical(df['model_name'], categories=ordered_model_names, ordered=True)

df.head()

# %% [markdown]
# ### 2. Overall Architecture Comparison: Native Vision vs. OCR+LLM
# Let's look at the absolute success rate grouped by model.

# %%
agg_df = df.groupby('model_name', observed=False).agg(
    accuracy=('is_perfect_run', 'mean'),
    avg_time=('total_time', 'mean'),
    family=('model_family', 'first')
).reset_index()

# Sort by accuracy
agg_df = agg_df.sort_values('model_name')

plt.figure(figsize=(10, 6))
ax = sns.barplot(data=agg_df, x='accuracy', y='model_name', hue='family', dodge=False)
ax.set_title("Overall Accuracy", fontweight='bold')
ax.set_xlabel("Accuracy")
ax.set_ylabel("")
ax.set_xlim(0, 1.05)

# Annotate percentages
for p in ax.patches:
    width = p.get_width()
    if width > 0:
        ax.text(width + 0.01, p.get_y() + p.get_height()/2., f'{width:.1%}', ha="left", va="center")

plt.tight_layout()
# plt.savefig("overall_accuracy.svg")
plt.show()

# %% [markdown]
# ### 3. Inference Time & Processing Pipeline Cost
# How much overhead does the Tesseract OCR layer add compared to a native VLM approach?

# %%
time_df = df.groupby('model_name', observed=False)[['tesseract_time', 'llama_time', 'total_time']].mean().reset_index()
time_df = time_df.sort_values('model_name')

fig, ax = plt.subplots(figsize=(10, 6))

time_df['bar1_tesseract'] = time_df['tesseract_time'].fillna(0)
time_df['bar2_llm'] = time_df.apply(lambda r: r['total_time'] if pd.isnull(r['llama_time']) else r['llama_time'], axis=1)

y_pos = np.arange(len(time_df))
model_names_str = time_df['model_name'].astype(str).tolist()

ax.barh(y_pos, time_df['bar1_tesseract'], color='#DD8452', label='OCR Time (Tesseract)')
ax.barh(y_pos, time_df['bar2_llm'], left=time_df['bar1_tesseract'], color='#4C72B0', label='LLM/VLM Time (Llama/Qwen)')

ax.set_yticks(y_pos)
ax.set_yticklabels(model_names_str)
ax.invert_yaxis()  # Put the first grouped model at the top

# Add text for total time
for i, total in enumerate(time_df['total_time']):
    if pd.notnull(total):
        ax.text(total + 0.2, i, f'{total:.1f}s', ha='left', va='center')

ax.set_title("Average Inference Time", fontweight='bold')
ax.set_xlabel("Time (seconds)")
ax.legend(loc='lower right')
plt.tight_layout()
# plt.savefig("average_inference_time.svg")
plt.show()

# %% [markdown]
# ### 4. Latency Stability (Boxplots)
# Averages hide outliers. We need to ensure models behave predictably on edge devices.

# %%
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='total_time', y='model_name', hue='model_family', showfliers=True)
plt.title("Inference Time Distribution", fontweight='bold')
plt.xlabel("Total Time (seconds)")
plt.ylabel("")
plt.tight_layout()
# plt.savefig("inference_time_distribution.svg")
plt.show()

# %% [markdown]
# ### 5. Robustness to Noise (Image Quality)
# How well do different models handle bad camera captures (blurry / cut off)?

# %%
quality_df = df.groupby(['model_name', 'image_selection'], observed=False)['is_perfect_run'].mean().unstack()

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
# plt.savefig("model_robustness_heatmap.svg")
plt.show()

# %% [markdown]
# ### 6. Failure Mode Analysis
# When a model fails, does it hallucinate JSON (Match Found = False), extract the wrong recipient, or pick the wrong image?

# %%
def categorize_failure(row):
    if row['is_perfect_run']:
        return 'Success'
    elif row['error_msg']:
        if row['error_msg'].startswith('Error at correct recipients ID check'):
            return 'Failed: Wrong Recipient'
        elif row['error_msg'].startswith('Error at correct image ID check'):
            return 'Failed: Wrong Best Image'
        elif row['error_msg'].startswith('JSON/Schema Error'):
            return 'Failed: Invalid JSON / Schema'
        else:
            return 'Failed: Other'
    else:
        return 'Failed: Other'

df['outcome'] = df.apply(categorize_failure, axis=1)

outcome_counts = df.groupby(['model_name', 'outcome'], observed=False).size().unstack(fill_value=0)

# Isolate failures only
if 'Success' in outcome_counts.columns:
    outcome_counts = outcome_counts.drop(columns=['Success'])

# Convert to percentages relative to total failures per model
outcome_pct = outcome_counts.div(outcome_counts.sum(axis=1).replace(0, np.nan), axis=0) * 100
outcome_pct = outcome_pct.fillna(0)

# Enforce consistent column coloring and ordering
desired_order = ['Failed: Wrong Recipient', 'Failed: Wrong Best Image', 'Failed: Invalid JSON / Schema','Failed: Other']
desired_order.reverse()
existing_cols = [c for c in desired_order if c in outcome_pct.columns]
outcome_pct = outcome_pct[existing_cols]

color_map = {
    'Failed: Invalid JSON / Schema': '#D62728',
    'Failed: Wrong Recipient': '#E66101',
    'Failed: Wrong Best Image': '#F4A582',
    'Failed: Other': '#7F7F7F'
}
plot_colors = [color_map[c] for c in outcome_pct.columns]

ax_fail = outcome_pct.plot(kind='bar', stacked=True, color=plot_colors, figsize=(12, 7))

# Add percentages inside the bars for readability
for c in ax_fail.containers:
    labels = [f'{v.get_height():.1f}%' if v.get_height() > 0.0 else '' for v in c]
    ax_fail.bar_label(c, labels=labels, label_type='center', fontsize=9, color='white', weight='bold')

plt.title("Failure Distribution", fontweight='bold')
plt.xlabel("Model")
plt.ylabel("Percentage of Failures (%)")
plt.xticks(rotation=45, ha='right')
plt.legend(title='Outcome', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
# plt.savefig("failure_distribution.svg")
plt.show()

# %% [markdown]
# ### 7. The Pareto Frontier: Speed vs. Accuracy
# Identify the optimal models for production based on edge-device constraints.

# %%
plt.figure(figsize=(13, 7))
sns.scatterplot(data=agg_df, x='avg_time', y='accuracy', hue='family', s=150, style='family')

# Annotate points
for i, row in agg_df.iterrows():
    if pd.notnull(row['avg_time']) and pd.notnull(row['accuracy']):
        plt.annotate(f"{row['model_name']}\n({row['avg_time']:.1f}s, {row['accuracy']:.1%})",
                     (row['avg_time'], row['accuracy']),
                     xytext=(8, -10), textcoords='offset points', fontsize=9)

plt.title("Speed vs. Accuracy", fontweight='bold')
plt.xlabel("Average Inference Time (seconds)")
plt.ylabel("Accuracy")
plt.ylim(0, 1.05)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
# plt.savefig("speed_vs_accuracy.svg")
plt.show()

# %% [markdown]
# ### 8. Scaling Laws (Model Size vs Accuracy)
# Performance returns as model parameter count increases.

# %%
qwen_df = agg_df[(agg_df['family'] == 'ModelFamily.Qwen3') | (agg_df['model_name'].astype(str).str.contains('qwen'))].copy()
qwen_df['params'] = qwen_df['model_name'].astype(str).apply(extract_params)
qwen_df = qwen_df[qwen_df['params'] > 0].dropna(subset=['params']).sort_values('params')

llama_df = agg_df[(agg_df['family'] == 'ModelFamily.Llama') | (agg_df['model_name'].astype(str).str.contains('llama'))].copy()
llama_df['params'] = llama_df['model_name'].astype(str).apply(extract_params)
llama_df = llama_df[llama_df['params'] > 0].dropna(subset=['params']).sort_values('params')

if not qwen_df.empty or not llama_df.empty:
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    if not qwen_df.empty:
        ax1.plot(qwen_df['params'], qwen_df['accuracy'], marker='o', color='#2CA02C', linewidth=2, markersize=10, label='Qwen3.5 (Native VLM)')
        for i, row in qwen_df.iterrows():
            ax1.annotate(f"{row['accuracy']:.1%}", (row['params'], row['accuracy']),
                         xytext=(0, 10), textcoords='offset points', ha='center', fontsize=10)
                         
    if not llama_df.empty:
        ax1.plot(llama_df['params'], llama_df['accuracy'], marker='s', color='#DD8452', linewidth=2, markersize=10, label='Llama + Tesseract')
        for i, row in llama_df.iterrows():
            ax1.annotate(f"{row['accuracy']:.1%}", (row['params'], row['accuracy']),
                         xytext=(0, -15), textcoords='offset points', ha='center', fontsize=10)

    ax1.set_title("Model Scaling", fontweight='bold')
    ax1.set_xlabel("Parameters (Billions) - Log Scale")
    ax1.set_ylabel("Accuracy Rate")
    ax1.set_xscale('log')
    ax1.legend(loc='lower right')
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    # plt.savefig("model_scaling.svg")
    plt.show()