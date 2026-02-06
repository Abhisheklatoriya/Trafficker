import streamlit as st
import pandas as pd

st.set_page_config(page_title="Offer Prefill Tool", layout="wide")

st.title("📦 Offer Trafficking Prefill Tool")
st.caption("Upload Asset Matrix + Copy Deck → Generate trafficking-ready rows")

# ---------------------------------------------------
# Uploads
# ---------------------------------------------------
asset_file = st.file_uploader("Upload Asset Matrix (xlsx)", type=["xlsx"])
copy_file = st.file_uploader("Upload Copy Deck (xlsx)", type=["xlsx"])

if not asset_file or not copy_file:
    st.info("Upload both files to continue")
    st.stop()

asset_df = pd.read_excel(asset_file)
copy_df = pd.read_excel(copy_file)

st.success("Files loaded successfully")

# ---------------------------------------------------
# 🔑 CONFIG — EDIT THIS SECTION ONLY
# ---------------------------------------------------

# Columns used to MATCH asset matrix ↔ copy deck
JOIN_KEYS = {
    "Messaging": "Messaging",
    "Region": "Region",
    "Offer Type": "Offer Type"
}

# Columns extracted from ASSET MATRIX
ASSET_COLUMNS = {
    "Start Date": "Start Date",
    "End Date": "End Date",
    "Landing Page URL": "Landing Page URL",
    "Messaging": "Messaging",
    "Offer Type": "Offer Type",
    "Region": "Region"
}

# Columns extracted from COPY DECK
COPY_COLUMNS = {
    "Message Copy": "Message Copy",
    "Headline Copy": "Headline Copy",
    "Desc. Copy": "Desc. Copy",
    "CTA": "CTA",
    "Hashtag": "Hashtag",
    "Display URL": "Display URL"
}

# Columns you want in the FINAL OUTPUT (green columns only)
OUTPUT_COLUMNS = [
    "Ready?",
    "Status",
    "Start Date",
    "End Date",
    "Creative Concept",
    "Platform",
    "Offer Type",
    "Messaging",
    "Message Copy",
    "Headline Copy",
    "Desc. Copy",
    "CTA",
    "Landing Page URL",
    "Hashtag",
    "Display URL"
]

# ---------------------------------------------------
# Normalization (prevents mismatch issues)
# ---------------------------------------------------
def normalize(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.lower()
    return df

asset_df = normalize(asset_df, JOIN_KEYS.keys())
copy_df = normalize(copy_df, JOIN_KEYS.values())

# ---------------------------------------------------
# Merge Logic
# ---------------------------------------------------
merged = asset_df.copy()

merged = merged.merge(
    copy_df,
    how="left",
    left_on=list(JOIN_KEYS.keys()),
    right_on=list(JOIN_KEYS.values()),
    suffixes=("", "_copy")
)

# ---------------------------------------------------
# Build Output Rows
# ---------------------------------------------------
output_rows = []

for _, row in merged.iterrows():
    out = {}

    missing = []

    # Asset-based fields
    for out_col, asset_col in ASSET_COLUMNS.items():
        val = row.get(asset_col, "")
        out[out_col] = val
        if pd.isna(val) or val == "":
            missing.append(out_col)

    # Copy-based fields
    for out_col, copy_col in COPY_COLUMNS.items():
        val = row.get(copy_col, "")
        out[out_col] = val
        if pd.isna(val) or val == "":
            missing.append(out_col)

    # Fixed / derived fields (customize if needed)
    out["Platform"] = row.get("Platform", "")
    out["Creative Concept"] = row.get("Creative Concept", "")

    # Status
    if missing:
        out["Ready?"] = "No"
        out["Status"] = f"Missing: {', '.join(missing)}"
    else:
        out["Ready?"] = "Yes"
        out["Status"] = "Ready"

    output_rows.append(out)

output_df = pd.DataFrame(output_rows)

# Ensure output column order
output_df = output_df.reindex(columns=OUTPUT_COLUMNS)

# ---------------------------------------------------
# Preview
# ---------------------------------------------------
st.subheader("🔍 Preview")
st.dataframe(output_df, use_container_width=True)

# ---------------------------------------------------
# Download
# ---------------------------------------------------
st.subheader("⬇️ Download")
csv = output_df.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Trafficking Prefill CSV",
    csv,
    file_name="offer_prefill_output.csv",
    mime="text/csv"
)

