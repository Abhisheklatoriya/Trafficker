import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Traffic Sheet Builder", layout="wide")
st.title("🏗️ Traffic Sheet Builder")

# ---------------------------------------------------------
# 1. Session State (The "Memory" of the app)
# ---------------------------------------------------------
if "rows" not in st.session_state:
    st.session_state["rows"] = []

# Define the columns we want in our final file
OUTPUT_COLUMNS = [
    "Status", "Start Date", "End Date", "Platform", "Offer Type", 
    "Creative Name", "Ad Name", "Landing Page URL", 
    "Headline", "Body Copy", "CTA", "Display URL"
]

# ---------------------------------------------------------
# 2. Sidebar: Global Defaults (Save time)
# ---------------------------------------------------------
with st.sidebar:
    st.header("Global Defaults")
    st.caption("Set these once to pre-fill the form.")
    
    d_start = st.date_input("Default Start Date", value=date.today())
    d_end   = st.date_input("Default End Date", value=date.today())
    d_plat  = st.selectbox("Default Platform", ["Facebook", "Google Search", "TikTok", "Display", "Email"])
    
    st.divider()
    
    # Action Buttons
    if st.button("🗑️ Clear All Rows"):
        st.session_state["rows"] = []
        st.rerun()

# ---------------------------------------------------------
# 3. The Builder Form
# ---------------------------------------------------------
st.subheader("1) Build a Row")

# We use a container so we can separate visual layout from logic
with st.container(border=True):
    
    # Row 1: Logistics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        start_date = st.date_input("Start Date", value=d_start)
    with c2:
        end_date = st.date_input("End Date", value=d_end)
    with c3:
        platform = st.selectbox("Platform", ["Facebook", "Google Search", "TikTok", "Display", "Email"], index=["Facebook", "Google Search", "TikTok", "Display", "Email"].index(d_plat))
    with c4:
        offer_type = st.selectbox("Offer Type", ["Generic", "Seasonal", "Retargeting", "Promo"])

    # Row 2: Creative Identifiers
    c1, c2 = st.columns(2)
    with c1:
        creative_name = st.text_input("Creative Name / Concept", placeholder="e.g. Q1_Promo_Blue_Hero")
    with c2:
        ad_name = st.text_input("Ad Name (System ID)", placeholder="e.g. FB_Q1_PROMO_001")

    # Row 3: URLs
    url = st.text_input("Landing Page URL", placeholder="https://...")

    # Row 4: Copy
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        headline = st.text_input("Headline", max_chars=30, help="Max 30 chars usually")
        cta = st.selectbox("CTA Button", ["Shop Now", "Learn More", "Sign Up", "Get Offer"])
    with c2:
        body = st.text_area("Body Copy / Description", max_chars=125)
        display_url = st.text_input("Display URL (Vanity)", placeholder="example.com/offers")

    # Buttons
    b1, b2, b3 = st.columns([1, 1, 4])
    
    # Logic to add the row
    if b1.button("➕ Add Row", type="primary"):
        new_row = {
            "Start Date": start_date,
            "End Date": end_date,
            "Platform": platform,
            "Offer Type": offer_type,
            "Creative Name": creative_name,
            "Ad Name": ad_name,
            "Landing Page URL": url,
            "Headline": headline,
            "Body Copy": body,
            "CTA": cta,
            "Display URL": display_url,
        }
        
        # Simple Validation Logic
        missing = [k for k, v in new_row.items() if not v]
        if missing:
            new_row["Status"] = f"⚠️ Missing: {', '.join(missing)}"
        else:
            new_row["Status"] = "✅ Ready"
            
        st.session_state["rows"].append(new_row)
        st.success("Row added!")
        
    # Logic to duplicate the last row (Super helpful for speed)
    if b2.button("pV Duplicate Last"):
        if len(st.session_state["rows"]) > 0:
            last = st.session_state["rows"][-1].copy()
            st.session_state["rows"].append(last)
            st.info("Duplicated last row.")
        else:
            st.warning("Nothing to duplicate yet.")

# ---------------------------------------------------------
# 4. The Live Queue (Editable)
# ---------------------------------------------------------
st.subheader("2) Review & Export")

if len(st.session_state["rows"]) > 0:
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(st.session_state["rows"])
    
    # Reorder columns to match our desired output
    # (Ensure all columns exist just in case)
    for c in OUTPUT_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    df = df[OUTPUT_COLUMNS]

    # Show Editable Dataframe
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic",  # Allows user to delete rows
        use_container_width=True,
        column_config={
            "Status": st.column_config.TextColumn(disabled=True), # Status is auto-calc
        }
    )
    
    # Calculate stats
    ready = edited_df[edited_df["Status"] == "✅ Ready"].shape[0]
    total = edited_df.shape[0]
    
    st.write(f"**Total Rows:** {total} | **Ready:** {ready}")

    # Export
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download CSV",
        data=csv,
        file_name="traffic_sheet_output.csv",
        mime="text/csv",
        type="primary"
    )

else:
    st.info("Your list is empty. Add a row above to get started.")
