"""
Atlas AI Command Center - Streamlit Dashboard
MLOps monitoring interface for tracking AI model performance.
"""
import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="Atlas AI Command Center",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2d4a6f;
    }
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Atlas AI Command Center")
st.markdown("### مراقبة أداء الذكاء الاصطناعي (MLOps Monitoring)")


@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="atlas-db",
        database="atlas_production",
        user="atlas_admin",
        password="Atlas_Secure_2026"
    )


try:
    conn = get_connection()

    # Fetch data
    df_preds = pd.read_sql(
        "SELECT * FROM ai_predictions ORDER BY timestamp DESC LIMIT 1000",
        conn
    )
    df_feed = pd.read_sql("SELECT * FROM ai_feedback", conn)
    df_models = pd.read_sql(
        "SELECT * FROM ai_models ORDER BY deployed_at DESC",
        conn
    )

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    active_model = df_models[df_models['status'] == 'ACTIVE']
    model_version = active_model['version'].iloc[0] if not active_model.empty else "N/A"

    total_preds = len(df_preds)
    positive_fb = len(df_feed[df_feed['actual_feedback'] == 'positive'])
    negative_fb = len(df_feed[df_feed['actual_feedback'] == 'negative'])
    total_fb = positive_fb + negative_fb
    accuracy = (positive_fb / total_fb * 100) if total_fb > 0 else 100

    col1.metric("🤖 Model Version", model_version)
    col2.metric("📊 Total Predictions", total_preds)
    col3.metric("👍 Positive Feedback", positive_fb)
    col4.metric("🎯 AI Accuracy", f"{accuracy:.1f}%")

    st.divider()

    # Charts
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Decision Distribution")
        if not df_preds.empty:
            fig_pie = px.pie(
                df_preds,
                names='decision',
                title='Approved vs Blocked',
                color_discrete_sequence=['#10B981', '#EF4444'],
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No predictions yet")

    with c2:
        st.subheader("📊 Risk Score Distribution")
        if not df_preds.empty and 'risk_score' in df_preds.columns:
            fig_hist = px.histogram(
                df_preds,
                x="risk_score",
                nbins=20,
                title="Risk Score Frequency",
                color_discrete_sequence=['#3B82F6']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No risk data yet")

    st.divider()

    # Drift Detection
    st.subheader("🔴 Negative Feedback (Drift Detection)")

    if not df_feed.empty:
        negative_cases = df_feed[df_feed['actual_feedback'] == 'negative']
        if not negative_cases.empty:
            st.error(f"⚠️ {len(negative_cases)} cases flagged for review!")

            # Merge with predictions for context
            if not df_preds.empty:
                merged = pd.merge(
                    negative_cases,
                    df_preds,
                    left_on='prediction_id',
                    right_on='id',
                    how='left'
                )
                display_cols = ['timestamp_x', 'prediction_id', 'input_context',
                                'risk_score', 'decision', 'correction_note']
                available_cols = [c for c in display_cols if c in merged.columns]
                st.dataframe(merged[available_cols], use_container_width=True)
        else:
            st.success("✅ No drift detected. Model performing well!")
    else:
        st.info("No feedback data yet")

    st.divider()

    # Recent Predictions
    st.subheader("📋 Recent Predictions")
    if not df_preds.empty:
        st.dataframe(
            df_preds[['id', 'model_version', 'input_context', 'risk_score',
                      'decision', 'timestamp']].head(20),
            use_container_width=True
        )

    # Retrain Button
    st.divider()
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Trigger Model Retraining", use_container_width=True):
            st.toast("Starting retraining pipeline...", icon="⚙️")
            st.balloons()
            st.success("Retraining job queued! (Simulation)")

except Exception as e:
    st.error(f"Database connection error: {e}")
    st.info("Make sure the database is running and tables are initialized.")
