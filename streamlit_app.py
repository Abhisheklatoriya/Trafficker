import streamlit as st
import pandas as pd

st.set_page_config(page_title="Offer Prefill Tool", layout="wide")
st.title("📦 Offer Trafficking Prefill Tool")

# ----------------------------
# Helpers
# ----------------------------
def clean_colnames(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def norm_series(s: pd.Series) -> pd.Series:
    # normalize for matching: lower, strip, collapse whitespace; keep NA
    return (
        s.astype("string")
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )

def safe_get(row, col):
    return "" if col is None or col == "" else row.get(col, "")

# ----------------------------
# Uploads
# ----------------------------
asset_file = st.file_uploader("Upload Asset Matrix (xlsx/csv)", type=["xlsx", "csv"])
copy_file  = st.file_uploader("Upload Copy Deck (xlsx/csv)", type=["xlsx", "csv"])

if not asset_file or not copy_file:
    st.info("Upload both files to continue.")
    st.stop()

def read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file)

asset_df = clean_colnames(read_any(asset_file))
copy_df  = clean_colnames(read_any(copy_file))

st.success("Files loaded.")

with st.expander("🔎 See detected columns"):
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Asset Matrix columns**")
        st.write(list(asset_df.columns))
    with c2:
        st.write("**Copy Deck columns**")
        st.write(list(copy_df.columns))

# ----------------------------
# Step 1: Choose JOIN keys (UI)
# ----------------------------
st.subheader("1) Choose how to match Asset Matrix ↔ Copy Deck")

st.caption("Pick the columns that represent the same idea in both files (e.g., Region + Messaging + Offer Type).")

asset_cols = list(asset_df.columns)
copy_cols  = list(copy_df.columns)

# You can increase/decrease number of join keys easily
num_keys = st.slider("How many join keys?", min_value=1, max_value=6, value=3)

join_pairs = []
for i in range(num_keys):
    c1, c2 = st.columns(2)
    with c1:
        a_col = st.selectbox(f"Asset join column #{i+1}", asset_cols, key=f"a_join_{i}")
    with c2:
        b_col = st.selectbox(f"Copy join column #{i+1}", copy_cols, key=f"b_join_{i}")
    join_pairs.append((a_col, b_col))

# Validate uniqueness (avoid accidental duplicates)
asset_join_cols = [a for a, _ in join_pairs]
copy_join_cols  = [b for _, b in join_pairs]

if len(set(asset_join_cols)) != len(asset_join_cols) or len(set(copy_join_cols)) != len(copy_join_cols):
    st.error("Join columns contain duplicates. Choose unique columns for each join key.")
    st.stop()

# Normalize join columns to reduce mismatch due to casing/spaces
asset_norm = asset_df.copy()
copy_norm  = copy_df.copy()

for a, b in join_pairs:
    asset_norm[a] = norm_series(asset_norm[a])
    copy_norm[b]  = norm_series(copy_norm[b])

# ----------------------------
# Step 2: Map output fields (green columns)
# ----------------------------
st.subheader("2) Map the fields you want to prefill (green columns only)")

st.caption("If a field doesn’t exist in a file, set it to '(leave blank)'.")

LEAVE_BLANK = "(leave blank)"
asset_map_options = [LEAVE_BLANK] + asset_cols
copy_map_options  = [LEAVE_BLANK] + copy_cols

# These are your “green” output fields (edit as needed)
OUTPUT_COLUMNS = [
    "Ready?",
    "Status",
    "Start Date",
    "End Date",
    "Creative Concept",
    "Platform",
    "Offer Type",
    "Segments",
    "Creative Name",
    "Messaging",
    "Ad Name",
    "Concept Code",
    "Message Copy",
    "Headline Copy",
    "Desc. Copy",
    "CTA",
    "Landing Page URL",
    "Hashtag",
    "Display URL",
]

# Default mapping guesses (safe — may not match your real headers)
default_asset_guess = {
    "Start Date": "Start Date",
    "End Date": "End Date",
    "Landing Page URL": "Landing Page URL",
    "Platform": "Platform",
    "Offer Type": "Offer Type",
    "Messaging": "Messaging",
    "Segments": "Segments",
    "Creative Concept": "Creative Concep
