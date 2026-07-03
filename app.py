# ============================================================================
#  SELECTION DASHBOARD  -  STARTER APP  (MVP)
#  Brand colors: DoorDash = red, Uber Eats = green.
#  Three views: Selection, Exclusives, Delivery fee.  (No Google reviews for now.)
#  Shows the latest month AND how it moved vs the previous month.
# ============================================================================
#  RUN IT:
#     1.  pip install streamlit pandas openpyxl altair
#     2.  keep this file + Dashboard_Sample_Data.xlsx in the same folder
#     3.  streamlit run app.py
# ============================================================================

import streamlit as st
import pandas as pd
import altair as alt

DD_RED, UE_GREEN = "#FF3008", "#06C167"
UP, DOWN, INK, MUT = "#0E9F6E", "#E02424", "#17181A", "#6B7280"

# ---- 1. LOAD (one row per metro PER MONTH) ---------------------------------
df = pd.read_excel("Dashboard_Sample_Data.xlsx", sheet_name="dashboard_table", header=2)

# ---- 2. STYLING ------------------------------------------------------------
st.set_page_config(page_title="Selection Dashboard", layout="wide", page_icon="\U0001F37D")
st.markdown(f"""
<style>
  .block-container {{ padding-top: 2rem; max-width: 1250px; }}
  .title {{ font-size: 30px; font-weight: 800; color:{INK}; margin-bottom:2px; }}
  .sub   {{ color:{MUT}; font-size:14px; margin-bottom:14px; }}
  .kpi   {{ background:#fff; border:1px solid #E6E8EC; border-radius:14px; padding:16px 18px;
            box-shadow:0 1px 3px rgba(0,0,0,.05); }}
  .kpi .big {{ font-size:24px; font-weight:800; }} .kpi .lbl {{ color:{MUT}; font-size:12.5px; }}
  .grp {{ font-size:18px; font-weight:700; color:{INK}; margin:6px 0 0 0; }}
  .grpsub {{ color:{MUT}; font-size:12px; margin-bottom:2px; }}
  .row {{ font-size:13px; color:{INK}; margin:8px 0 0 0; }}
  .chip {{ font-size:11px; font-weight:700; }}
  .dot {{ height:11px; width:11px; border-radius:50%; display:inline-block; margin-right:6px; }}
</style>""", unsafe_allow_html=True)

# ---- 3. HEADER + PERIOD PICKER (this is the "over time" control) -----------
periods = sorted(df["period"].unique(), reverse=True)          # newest first
c_title, c_period = st.columns([3, 1])
with c_title:
    st.markdown('<div class="title">Selection Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub"><span class="dot" style="background:{DD_RED}"></span>DoorDash'
                f'&nbsp;&nbsp;<span class="dot" style="background:{UE_GREEN}"></span>Uber Eats'
                f'&nbsp;&nbsp;\u00b7&nbsp;&nbsp;restaurant choice by metro</div>', unsafe_allow_html=True)
with c_period:
    current = st.selectbox("Month", periods, index=0)
# comparison month = the one right before "current"
older = [p for p in periods if p < current]
compare = older[0] if older else current
st.caption(f"Showing **{current}** and how it moved vs **{compare}**." if compare != current
           else f"Showing **{current}** (no earlier month to compare yet).")

cur  = df[df["period"] == current].set_index("CBSA")
prev = df[df["period"] == compare].set_index("CBSA")

# ---- 4. THE THREE VIEWS ----------------------------------------------------
VIEWS = {
    "Selection":    dict(dd="DD_restaurants", ue="UE_restaurants", fmt="{:,.0f}", note="number of restaurants each app offers"),
    "Exclusives":   dict(dd="DD_exclusive",   ue="UE_exclusive",   fmt="{:,.0f}", note="restaurants available on one app only"),
    "Delivery fee": dict(dd="DD_avg_fee",     ue="UE_avg_fee",     fmt="${:,.2f}", note="average delivery fee (lower is cheaper)"),
}
view = st.radio("View", list(VIEWS.keys()), horizontal=True, label_visibility="collapsed")
cfg = VIEWS[view]
st.caption("Showing: " + cfg["note"])

def gap(row):     # DoorDash minus Uber Eats
    return row[cfg["dd"]] - row[cfg["ue"]]

# ---- 5. KPI TILES (with movement) ------------------------------------------
leads = sum(gap(cur.loc[m]) >= 0 for m in cur.index)
widened = sum((gap(cur.loc[m]) - gap(prev.loc[m])) > 0 for m in cur.index if m in prev.index)
est = (cur["ue_data"] == "estimated").sum()
k1, k2, k3 = st.columns(3)
k1.markdown(f'<div class="kpi"><div class="big" style="color:{DD_RED}">{leads} of {len(cur)}</div>'
            f'<div class="lbl">metros where DoorDash leads on {view.lower()}</div></div>', unsafe_allow_html=True)
k2.markdown(f'<div class="kpi"><div class="big" style="color:{UP}">widened in {widened}</div>'
            f'<div class="lbl">metros where DoorDash\u2019s gap grew vs {compare}</div></div>', unsafe_allow_html=True)
k3.markdown(f'<div class="kpi"><div class="big" style="color:{UE_GREEN}">{est} of {len(cur)}</div>'
            f'<div class="lbl">metros using estimated (dummy) Uber data</div></div>', unsafe_allow_html=True)
st.write("")

# ---- 6. THREE GROUP COLUMNS, each metro shows bars + "vs last month" --------
groups = ["DoorDash-dominant", "Battleground", "Uber Eats-dominant"]
cols = st.columns(3)
for box, group in zip(cols, groups):
    with box:
        sub = cur[cur["Group"] == group]
        st.markdown(f'<div class="grp">{group}</div>', unsafe_allow_html=True)
        st.markdown('<div class="grpsub">&nbsp;</div>', unsafe_allow_html=True)
        for metro, r in sub.iterrows():
            # bars for the current month
            cd = pd.DataFrame([{"app": "DoorDash", "value": r[cfg["dd"]]},
                               {"app": "Uber Eats", "value": r[cfg["ue"]]}])
            ch = (alt.Chart(cd).mark_bar(cornerRadiusEnd=3, height=12)
                  .encode(x=alt.X("value:Q", title=None),
                          y=alt.Y("app:N", title=None, sort=["DoorDash", "Uber Eats"]),
                          color=alt.Color("app:N", legend=None,
                              scale=alt.Scale(domain=["DoorDash", "Uber Eats"], range=[DD_RED, UE_GREEN])),
                          tooltip=["app", "value"])
                  .properties(height=70))
            # movement chip vs previous month
            if metro in prev.index:
                d = gap(r) - gap(prev.loc[metro])
                arrow, col = ("\u25B2", UP) if d >= 0 else ("\u25BC", DOWN)
                move = f'<span class="chip" style="color:{col}">{arrow} {abs(d):.0f} vs {compare}</span>'
            else:
                move = ""
            tag = "  ·  est." if r["ue_data"] == "estimated" else ""
            st.markdown(f'<div class="row"><b>{metro}</b>{tag}&nbsp;&nbsp;{move}</div>', unsafe_allow_html=True)
            st.altair_chart(ch, use_container_width=True)

# ---- 7. NEXT STEPS ---------------------------------------------------------
st.divider()
st.info("Each month = one refresh: re-run the numbers and ADD rows with the new 'period'. "
        "The dashboard then compares the latest month to the one before automatically. "
        "Swap the sample for the real table (same columns), then deploy to Render.")
