import streamlit as st
import datetime
import pandas as pd
import db_utils

db_utils.init_dummy_db()

st.set_page_config(page_title="Site Manpower Logger", page_icon="🏗️", layout="wide")

# ─────────────────────────────────────────────
# DATES
# ─────────────────────────────────────────────
today_str    = datetime.date.today().strftime("%Y-%m-%d")
display_date = datetime.date.today().strftime("%d/%m/%Y")

APP_URL = "https://manpowerupdate-tnyp8osa8fcfycjstivc7x.streamlit.app/?embed_options=dark_theme"

# ─────────────────────────────────────────────
# AUTO-SCROLL JS (fires after button click)
# ─────────────────────────────────────────────
auto_scroll = """
<script>
setTimeout(function() {
    const el = document.getElementById('summary-top');
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}, 400);
</script>
"""

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🏗️ Site Manpower Logger")
st.caption(f"Today: {display_date}")

tab1, tab2 = st.tabs(["📋 Daily Manpower", "⏰ Overtime"])

# ═════════════════════════════════════════════
# TAB 1 — DAILY MANPOWER
# ═════════════════════════════════════════════
with tab1:

    # ── INPUT FORM ──
    supervisors = db_utils.get_supervisor_list()
    selected_sup = st.selectbox("Supervisor", supervisors, key="mp_sup")

    planned = db_utils.get_planned(selected_sup)
    st.caption(f"Planned headcount for {selected_sup}: **{planned}**")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        num_workers = st.number_input("Workers today", min_value=0, value=0, step=1, key="mp_count")
    with col_b:
        remarks = st.text_input(
            "Remarks (optional)",
            placeholder="e.g. 2 MC, 1 AL, 1 home leave",
            key="mp_remarks"
        )

    if num_workers > 0 and num_workers < planned:
        st.warning(f"⚠️ {planned - num_workers} worker(s) short of planned ({planned})")
    elif num_workers > planned and planned > 0:
        st.info(f"ℹ️ {num_workers - planned} above planned ({planned})")

    if st.button("Log & Update Summary", type="primary", key="mp_btn"):
        db_utils.log_daily_deployment(today_str, selected_sup, num_workers, remarks)
        st.success(f"✅ Saved — {selected_sup}: {num_workers} workers")
        st.markdown(auto_scroll, unsafe_allow_html=True)

    # ── SUMMARY ANCHOR ──
    st.markdown('<div id="summary-top"></div>', unsafe_allow_html=True)
    st.divider()

    # ── LIVE DATA ──
    filled_df, total, status_df, unfilled = db_utils.get_todays_summary(today_str)

    # Status banner
    if unfilled:
        st.warning(f"⏳ **{len(unfilled)} not yet logged:** {', '.join(unfilled)}")
    else:
        st.success("🎉 All supervisors logged for today!")

    # KPI row
    st.metric("Total Manpower Today", total)

    # Full status table
    st.subheader(f"📊 Submission Status — {display_date}")
    st.dataframe(status_df, use_container_width=True, hide_index=True)

    # ── EXPORT ──
    st.divider()
    col_exp1, col_exp2 = st.columns([1, 3])
    with col_exp1:
        excel_buf = db_utils.export_daily_excel(today_str)
        st.download_button(
            label="📥 Export to Excel",
            data=excel_buf,
            file_name=f"manpower_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="mp_export"
        )

    # ── WHATSAPP MESSAGES ──
    if not filled_df.empty:
        st.divider()
        st.subheader("📱 WhatsApp Messages")

        wa_tab1, wa_tab2 = st.tabs(["Summary", "Detail"])

        with wa_tab1:
            # Summary format matching the boss report style
            tmjp_rows  = filled_df[filled_df['Site'] == 'TMJP']
        #     brani_rows = filled_df[filled_df['Site'] == 'Brani']

        #     lines = ["*TMJP*", f"Daily Manpower", f"Date {display_date}", ""]
        #     for _, r in tmjp_rows.iterrows():
        #         sup_label = r['Supervisor'].replace('_', ' ')
        #         lines.append(f"{sup_label} = {r['Workers']}")
        #     if not tmjp_rows.empty:
        #         lines.append(f"*Total TMJP* = {int(tmjp_rows['Workers'].sum())}")

        #     if not brani_rows.empty:
        #         lines.append("")
        #         lines.append("*BRANI*")
        #         for _, r in brani_rows.iterrows():
        #             sup_label = r['Supervisor'].replace('_', ' ')
        #             lines.append(f"{sup_label} = {r['Workers']}")
        #         lines.append(f"*Total Brani* = {int(brani_rows['Workers'].sum())}")

        #     lines += ["", f"*Grand Total = {total}*",
        #               "\n----------------------------------------",
        #               f"⚠️ *Update via:* {APP_URL}"]
        #     st.code("\n".join(lines), language="text")

        with wa_tab1:
            # Detail format with remarks
            lines2 = [f"Daily Manpower Detail", f"Date: {display_date}", ""]
            for i, (_, r) in enumerate(filled_df.iterrows(), 1):
                sup_label = r['Supervisor'].replace('_', ' ')
                line = f"{i}. {sup_label} — {r['Workers']}"
                if r['Remarks']:
                    line += f" ({r['Remarks']})"
                lines2.append(line)
            lines2 += [f"\nTotal: {total}",
                       "----------------------------------------",
                       f"⚠️ *Update via:* {APP_URL}"]
            st.code("\n".join(lines2), language="text")


# ═════════════════════════════════════════════
# TAB 2 — OVERTIME
# ═════════════════════════════════════════════
with tab2:

    supervisors_ot = db_utils.get_supervisor_list()
    selected_sup_ot = st.selectbox("Supervisor", supervisors_ot, key="ot_sup")

    col_c, col_d = st.columns([1, 2])
    with col_c:
        num_ot = st.number_input("OT workers", min_value=0, value=0, step=1, key="ot_count")
    with col_d:
        remarks_ot = st.text_input(
            "Remarks (optional)",
            placeholder="e.g. OT 8am–10pm, 3 LHL 1 HB",
            key="ot_remarks"
        )

    if st.button("Log OT & Update Summary", type="primary", key="ot_btn"):
        db_utils.log_overtime(today_str, selected_sup_ot, num_ot, remarks_ot)
        st.success(f"✅ Saved — {selected_sup_ot}: {num_ot} OT workers")
        st.markdown(auto_scroll, unsafe_allow_html=True)

    st.markdown('<div id="summary-top"></div>', unsafe_allow_html=True)
    st.divider()

    filled_ot, total_ot, status_ot, unfilled_ot = db_utils.get_todays_ot_summary(today_str)

    if unfilled_ot:
        st.warning(f"⏳ **{len(unfilled_ot)} not yet logged OT:** {', '.join(unfilled_ot)}")
    else:
        st.success("All supervisors logged OT for today!")

    st.metric("Total OT Workers Today", total_ot)

    st.subheader(f"📊 OT Submission Status — {display_date}")
    st.dataframe(status_ot, use_container_width=True, hide_index=True)

    # Export button (reuses same daily export — both sheets included)
    st.divider()
    col_exp3, _ = st.columns([1, 3])
    with col_exp3:
        excel_buf_ot = db_utils.export_daily_excel(today_str)
        st.download_button(
            label="📥 Export to Excel",
            data=excel_buf_ot,
            file_name=f"manpower_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="ot_export"
        )

    if not filled_ot.empty:
        st.divider()
        st.subheader("📱 WhatsApp OT Message")

        ot_lines = [f"Overtime Manpower", f"Date: {display_date}", ""]
        for i, (_, r) in enumerate(filled_ot.iterrows(), 1):
            sup_label = r['Supervisor'].replace('_', ' ')
            line = f"{i}. {sup_label} — {r['OT Workers']}"
            if r['Remarks']:
                line += f" ({r['Remarks']})"
            ot_lines.append(line)
        ot_lines += [f"\nTotal OT: {total_ot}",
                     "----------------------------------------",
                     f"⚠️ *Update via:* {APP_URL}"]
        st.code("\n".join(ot_lines), language="text")
    else:
        st.info("No OT logged yet today.")
