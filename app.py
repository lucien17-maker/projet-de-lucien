import streamlit as st
import pandas as pd
from datetime import date
import plotly.express as px

st.set_page_config(page_title="E-commerce Daily Money System", layout="wide")

st.title("E-commerce Daily Money System")
st.caption("Plan quotidien + suivi KPI pour améliorer tes résultats.")

# ---------- Storage ----------
DATA_FILE = "ecommerce_daily.csv"

def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        # ensure types
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def save_row(row: dict):
    df = load_data()
    row_df = pd.DataFrame([row])
    if df.empty:
        out = row_df
    else:
        # replace same date if exists
        if row_df["date"].iloc[0] in df["date"].values:
            df = df[df["date"] != row_df["date"].iloc[0]]
        out = pd.concat([df, row_df], ignore_index=True)
    out.to_csv(DATA_FILE, index=False)

df = load_data()

# ---------- Sidebar ----------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Page", ["Aujourd’hui", "Suivi & Historique", "Paramètres"])

# ---------- Defaults / Checklist ----------
default_tasks = [
    "Vérifier stocks & expéditions (ruptures, délais)",
    "Publier/optimiser 1 contenu (TikTok/IG/FB/Shorts)",
    "Créer ou optimiser 1 campagne (Ads) / audience / créa",
    "Traiter messages clients (SAV) + relances",
    "Optimiser fiche produit (titre, photos, descriptions)",
    "Animer relances panier abandonné / email",
    "Analyser KPI (conversion, ROAS, top produits)"
]

# ---------- Page: Aujourd’hui ----------
if page == "Aujourd’hui":
    today = date.today()
    st.subheader(f"Plan du jour — {today}")

    col1, col2 = st.columns([1, 1])

    # Tasks
    with col1:
        st.markdown("### Checklist actions")
        tasks = st.session_state.get("tasks", default_tasks)
        # store checked state in session
        if "checked" not in st.session_state:
            st.session_state["checked"] = {t: False for t in tasks}

        for t in tasks:
            st.session_state["checked"][t] = st.checkbox(t, value=st.session_state["checked"][t])

        completion = sum(1 for v in st.session_state["checked"].values() if v) / len(tasks)

        st.progress(completion)
        st.caption(f"Progression : {completion*100:.0f}%")

    # KPI input
    with col2:
        st.markdown("### Tes KPI (pour progresser)")

        # prefill from df if today exists
        row_today = None
        if not df.empty and "date" in df.columns and today in df["date"].values:
            row_today = df[df["date"] == today].iloc[0].to_dict()

        def num_input(label, key, default=0.0, min_value=0.0, step=1.0):
            return st.number_input(label, min_value=min_value, step=step, value=float(row_today.get(key, default)) if row_today else default, key=key)

        sessions = num_input("Sessions (trafic)", "sessions", 0, 0, 1)
        orders = num_input("Commandes", "orders", 0, 0, 1)
        revenue = num_input("Chiffre d’affaires (€)", "revenue", 0, 0, 1)
        ads_cost = num_input("Budget Ads (€)", "ads_cost", 0, 0, 1)
        ad_sales = num_input("Ventes attribuées Ads (€)", "ad_sales", 0, 0, 1)
        returns = num_input("Retours / remboursements (€)", "returns", 0, 0, 1)

        # Derived metrics
        conversion = (orders / sessions) * 100 if sessions > 0 else 0
        roas = (ad_sales / ads_cost) if ads_cost > 0 else 0
        st.metric("Taux de conversion (%)", f"{conversion:.2f}%")
        st.metric("ROAS (Ventes Ads / coût Ads)", f"{roas:.2f}x")

        st.markdown("---")
        st.markdown("### Prochaine action recommandée")
        # Simple heuristic:
        rec = []
        if conversion < 1.5 and sessions > 200:
            rec.append("Améliore la page produit (UGC, photos avant/après, preuve sociale) + offre/promo.")
        if ads_cost > 0 and roas < 2:
            rec.append("Réduis le budget sur les créas faibles et teste 3 nouvelles variantes (angle + hook).")
        if orders == 0 and sessions > 0:
            rec.append("Revois la structure du site + preuve sociale + retargeting (abandons).")
        if returns > 0:
            rec.append("Regarde les raisons retours (tailles/attentes) et corrige la fiche + FAQ.")
        if not rec:
            rec.append("Continue : garde la régularité et optimise 1 levier par jour (produit, ads ou CRM).")

        st.write("• " + "\n• ".join(rec))

        if st.button("Enregistrer le suivi du jour", type="primary"):
            done_tasks = [k for k, v in st.session_state["checked"].items() if v]
            row = {
                "date": str(today),
                "sessions": sessions,
                "orders": orders,
                "revenue": revenue,
                "ads_cost": ads_cost,
                "ad_sales": ad_sales,
                "returns": returns,
                "conversion_pct": conversion,
                "roas": roas,
                "tasks_completed": "; ".join(done_tasks),
                "tasks_completion_ratio": completion
            }
            save_row(row)
            st.success("✅ Suivi enregistré !")
            st.rerun()

# ---------- Page: Suivi & Historique ----------
elif page == "Suivi & Historique":
    st.subheader("Historique KPI")

    if df.empty:
        st.info("Aucune donnée pour l’instant. Utilise la page “Aujourd’hui”.")
    else:
        df2 = df.copy()
        df2["date"] = pd.to_datetime(df2["date"]).dt.date

        c1, c2, c3 = st.columns(3)
        c1.metric("Jours enregistrés", len(df2))
        c2.metric("CA total (€)", f"{df2['revenue'].sum():,.0f}")
        c3.metric("Commandes totales", f"{df2['orders'].sum():,.0f}")

        # Charts
        st.markdown("### Chiffre d’affaires & Commandes")
        fig1 = px.line(df2.sort_values("date"), x="date", y="revenue", markers=True, title="CA par jour (€)")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(df2.sort_values("date"), x="date", y="orders", markers=True, title="Commandes par jour")
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### Conversion & ROAS")
        fig3 = px.line(df2.sort_values("date"), x="date", y="conversion_pct", markers=True, title="Conversion (%)")
        st.plotly_chart(fig3, use_container_width=True)

        fig4 = px.line(df2.sort_values("date"), x="date", y="roas", markers=True, title="ROAS (Ventes Ads / coût Ads)")
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown("---")
        st.markdown("### Export CSV")
        csv = df2.sort_values("date").to_csv(index=False).encode("utf-8")
        st.download_button("Télécharger l’historique CSV", csv, "ecommerce_daily_history.csv", "text/csv")

# ---------- Page: Paramètres ----------
else:
    st.subheader("Paramètres")
    st.info("Pour la V1, la checklist est fixe. Si tu me dis ton type d’e-commerce, je personnalise les tâches (Shopify, Amazon, dropshipping, niche, etc.).")

    st.markdown("### Tâches actuelles")
    st.write(default_tasks)
    st.caption("Prochaine étape : personnaliser par canal (Ads, TikTok, SEO, Email/SMS).")
    # Espace de séparation discret
st.markdown("---")

# Pied de page personnalisé
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 14px;'>"
    "Développé avec ❤️ par <b>LUCIEN 17</b> | E-commerce Daily Money System"
    "</div>", 
    unsafe_allow_html=True
)