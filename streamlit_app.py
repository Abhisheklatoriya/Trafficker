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
    val = row.get(col, "")
    return "" if pd.isna(val) or val is None else val

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

num_keys = st.slider("How many join keys?", min_value=1, max_value=6, value=3)

join_pairs = []
for i in range(num_keys):
    c1, c2 = st.columns(2)
    with c1:
        a_col = st.selectbox(f"Asset join column #{i+1}", asset_cols, key=f"a_join_{i}")
    with c2:
        b_col = st.selectbox(f"Copy join column #{i+1}", copy_cols, key=f"b_join_{i}")
    join_pairs.append((a_col, b_col))

# Create Normalized Temp Columns for Joining
# We do this to preserve the original formatting in the final output
asset_norm = asset_df.copy()
copy_norm  = copy_df.copy()

asset_join_keys = []
copy_join_keys = []

for i, (a, b) in enumerate(join_pairs):
    key_name_a = f"_join_key_asset_{i}"
    key_name_b = f"_join_key_copy_{i}"
    
    asset_norm[key_name_a] = norm_series(asset_norm[a])
    copy_norm[key_name_b]  = norm_series(copy_norm[b])
    
    asset_join_keys.append(key_name_a)
    copy_join_keys.append(key_name_b)

# ----------------------------
# Step 2: Map output fields
# ----------------------------
st.subheader("2) Map the fields you want to prefill (green columns only)")
st.caption("If a field doesn’t exist in a file, set it to '(leave blank)'.")

LEAVE_BLANK = "(leave blank)"
asset_map_options = [LEAVE_BLANK] + asset_cols
copy_map_options  = [LEAVE_BLANK] + copy_cols

OUTPUT_COLUMNS = [
    "Ready?", "Status", "Start Date", "End Date", "Creative Concept",
    "Platform", "Offer Type", "Segments", "Creative Name", "Messaging",
    "Ad Name", "Concept Code", "Message Copy", "Headline Copy",
    "Desc. Copy", "CTA", "Landing Page URL", "Hashtag", "Display URL",
]

# Helper for default selections
default_asset_guess = {
    "Start Date": "Start Date", "End Date": "End Date",
    "Landing Page URL": "Landing Page URL", "Platform": "Platform",
    "Offer Type": "Offer Type", "Messaging": "Messaging",
    "Segments": "Segments", "Creative Concept": "Creative Concept",
    "Creative Name": "Creative Name", "Ad Name": "Ad Name",
    "Concept Code": "Concept Code",
}
default_copy_guess = {
    "Message Copy": "Message Copy", "Headline Copy": "Headline Copy",
    "Desc. Copy": "Desc. Copy", "CTA": "CTA",
    "Hashtag": "Hashtag", "Display URL": "Display URL",
}

def pick_default(opts, guess):
    return guess if guess in opts else LEAVE_BLANK

with st.expander("🧩 Field mapping controls", expanded=True):
    colA, colB = st.columns(2)
    asset_field_map = {}
    copy_field_map = {}

    with colA:
        st.markdown("### From **Asset Matrix**")
        for out_field in [
            "Start Date","End Date","Landing Page URL","Platform","Offer Type","Messaging",
            "Segments","Creative Concept","Creative Name","Ad Name","Concept Code"
        ]:
            guess = default_asset_guess.get(out_field, "")
            sel = st.selectbox(
                f"{out_field} ←", asset_map_options,
                index=asset_map_options.index(pick_default(asset_map_options, guess)),
                key=f"map_asset_{out_field}"
            )
            asset_field_map[out_field] = None if sel == LEAVE_BLANK else sel

    with colB:
        st.markdown("### From **Copy Deck**")
        for out_field in ["Message Copy","Headline Copy","Desc. Copy","CTA","Hashtag","Display URL"]:
            guess = default_copy_guess.get(out_field, "")
            sel = st.selectbox(
                f"{out_field} ←", copy_map_options,
                index=copy_map_options.index(pick_default(copy_map_options, guess)),
                key=f"map_copy_{out_field}"
            )
            copy_field_map[out_field] = None if sel == LEAVE_BLANK else sel

# ----------------------------
# Step 3: Merge + Build Output
# ----------------------------
st.subheader("3) Generate output")

# We merge on the hidden normalized keys
merged = asset_norm.merge(
    copy_norm,
    how="left",
    left_on=asset_join_keys,
    right_on=copy_join_keys,
    suffixes=("", "_copy") 
    # ^ Colliding columns in Copy Deck get "_copy" suffix
    #   Colliding columns in Asset Matrix stay as is
)

output_rows = []
missing_required_fields = [
    "Start Date","End Date","Offer Type","Messaging","Message Copy",
    "Headline Copy","CTA","Landing Page URL"
]

for _, row in merged.iterrows():
    out = {}

    # 1. Fill from Asset (Standard Lookup)
    for field, col in asset_field_map.items():
        out[field] = safe_get(row, col)

    # 2. Fill from Copy (Smart Lookup)
    #    If column name collisions occurred, the copy version is now 'Name_copy'
    for field, col in copy_field_map.items():
        val = ""
        if col:
            # Check if a suffixed version exists (priority)
            suffixed_col = f"{col}_copy"
            if suffixed_col in row:
                val = row[suffixed_col]
            else:
                # Otherwise take the standard column
                val = row.get(col, "")
        
        out[field] = "" if pd.isna(val) else val

    # 3. Status Logic
    missing = []
    for req in missing_required_fields:
        val = out.get(req, "")
        if not val or str(val).strip() == "" or str(val).lower() == "nan":
            missing.append(req)

    if missing:
        out["Ready?"] = "No"
        out["Status"] = "Missing: " + ", ".join(missing)
    else:
        out["Ready?"] = "Yes"
        out["Status"] = "Ready"

    output_rows.append(out)

output_df = pd.DataFrame(output_rows)

# Ensure all columns exist
for c in OUTPUT_COLUMNS:
    if c not in output_df.columns:
        output_df[c] = ""

output_df = output_df[OUTPUT_COLUMNS]

# Preview
st.markdown("### Preview")
st.dataframe(output_df, use_container_width=True)

# Stats
ready_count = (output_df["Ready?"] == "Yes").sum()
needs_count = (output_df["Ready?"] != "Yes").sum()
st.write(f"✅ Ready: **{ready_count}** |  ⚠️ Needs Review: **{needs_count}**")

# Download
csv_bytes = output_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Prefill CSV",
    data=csv_bytes,
    file_name="offer_prefill_output.csv",
    mime="text/csv"
)
