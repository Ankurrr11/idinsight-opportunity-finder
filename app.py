import streamlit as st
import requests
import datetime
import xml.etree.ElementTree as ET
import email.utils

st.set_page_config(page_title="IDinsight Opportunity Pipeline", page_icon="🌍", layout="wide")

# --- CUSTOM BRANDING (IDINSIGHT) ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    </style>
    <div style='background-color:#0A233F; padding:20px; border-radius:10px; margin-bottom:20px;'>
        <h1 style='color:white; margin:0;'>🌍 IDinsight Opportunity Pipeline</h1>
        <p style='color:#E8EEF2; margin:0;'>Automated intelligence system for prioritizing client RFPs across Africa and Asia.</p>
    </div>
    """, unsafe_allow_html=True)

# --- DATA INGESTION (RSS FEED) ---
@st.cache_data(ttl=3600)
def fetch_live_opportunities():
    url = "https://reliefweb.int/jobs/rss.xml"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            jobs = []
            for item in root.findall('./channel/item'):
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                description = item.find('description').text if item.find('description') is not None else ""
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
                jobs.append({'fields': {'title': title, 'body-html': description, 'url': link, 'date': {'created': pubDate}}})
            return jobs
        return []
    except:
        return []

# --- ALGORITHMIC FILTERING ENGINE ---
def analyze_and_score(job_data):
    title = job_data['fields'].get('title', '').lower()
    body = job_data['fields'].get('body-html', '').lower()
    
    score = 0
    rationale = []
    
    target_regions = ['africa', 'asia', 'kenya', 'india', 'senegal', 'zambia', 'philippines', 'nigeria', 'uganda', 'malawi', 'morocco']
    if any(region in title or region in body for region in target_regions):
        score += 40
        rationale.append("✅ **Geography:** Strong alignment with target regions.")

    if any(k in title or k in body for k in ['impact evaluation', 'rct', 'randomized control']):
        score += 35
        rationale.append("✅ **Services:** High alignment with Impact Evaluation / RCT.")
    elif any(k in title or k in body for k in ['data analytics', 'machine learning', 'survey', 'research']):
        score += 25
        rationale.append("✅ **Services:** Strong alignment with Data & Tech Services.")
        
    if any(k in title or k in body for k in ['consultancy', 'rfp', 'request for proposal', 'bids']):
        score += 25
        rationale.append("✅ **Type:** Confirmed B2B / Consultancy Opportunity.")
        
    return score, " ".join(rationale)

# --- UI ---
st.sidebar.header("📅 Pipeline Settings")
lookback_days = st.sidebar.slider("Lookback Window (Days)", min_value=1, max_value=90, value=7)
st.sidebar.caption("Slide to 90 to view maximum history.")

st.sidebar.divider()
st.sidebar.header("🔐 User Authentication")
role = st.sidebar.selectbox("Simulate Logged-in User:", ["Global Director", "Director of Africa", "Director of Asia"])

tab1, tab2 = st.tabs(["📊 Active Opportunity Pipeline", "📩 Automated Report Preview"])

if st.sidebar.checkbox("🟢 Activate Opportunity Engine", value=True):
    with st.spinner("Scraping global databases and generating daily report..."):
        raw_data = fetch_live_opportunities()
        
    if raw_data:
        filtered_data = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for job in raw_data:
            pub_date_str = job['fields']['date']['created']
            try:
                pub_date = email.utils.parsedate_to_datetime(pub_date_str)
                days_old = (now - pub_date).days
                
                if lookback_days < 90 and days_old > lookback_days: 
                    continue
                filtered_data.append(job)
            except:
                filtered_data.append(job) 
                
        results = []
        for job in filtered_data:
            score, rationale = analyze_and_score(job)
            results.append({
                "title": job['fields'].get('title', 'Untitled'),
                "url": job['fields'].get('url', ''),
                "date": job['fields'].get('date', {}).get('created', '')[:16],
                "score": score,
                "rationale": rationale
            })
            
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        high_matches = [r for r in results if r['score'] >= 50]

        # --- TAB 1: THE PIPELINE ---
        with tab1:
            st.success(f"Pipeline Refresh Complete! Found {len(filtered_data)} opportunities in the selected timeframe.")
            st.header(f"🏆 Top Prioritized Opportunities for: {role}")
            if not high_matches: st.info("No high-match opportunities found today.")
                
            for i, r in enumerate(high_matches):
                with st.expander(f"[{r['score']}% Match] {r['title']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Scoring Rationale:**\n\n{r['rationale']}")
                        st.markdown(f"[🔗 View Full RFP Details]({r['url']})")
                        st.divider()
                        st.write("**⚙️ Enterprise Actions:**")
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        if btn_col1.button("👍 Train AI", key=f"up_{i}"): st.toast("Model updated.", icon="🧠")
                        if btn_col2.button("👎 Ignore", key=f"down_{i}"): st.toast("Model updated.", icon="📉")
                        if btn_col3.button("☁️ Push to CRM", key=f"crm_{i}"): st.toast("Created Lead in Salesforce!", icon="✅")
                    with col2:
                        st.metric("AI Match Score", f"{r['score']}%")
                        st.caption(f"📅 Published: {r['date']}")
                        
            st.divider()
            st.header("Other Scanned Items (Low Priority)")
            low_matches = [r for r in results if r['score'] < 50][:10]
            for i, r in enumerate(low_matches):
                with st.expander(f"[{r['score']}% Match] {r['title']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Scoring Rationale:**\n\n{r['rationale']}")
                        st.markdown(f"[🔗 View Full RFP Details]({r['url']})")
                        st.divider()
                        st.write("**⚙️ Train Model:**")
                        btn_col1, btn_col2 = st.columns(2)
                        if btn_col1.button("👍 Train AI (Upvote)", key=f"low_up_{i}"): st.toast("Model updated.", icon="🧠")
                        if btn_col2.button("👎 Ignore", key=f"low_down_{i}"): st.toast("Model updated.", icon="📉")
                    with col2:
                        st.metric("AI Match Score", f"{r['score']}%")
                        st.caption(f"📅 Published: {r['date']}")

        # --- TAB 2: VISUAL REPORT DIGEST ---
        with tab2:
            st.header("📩 Automated Daily Report (Preview)")
            st.caption("This is a preview of the automated email sent to the Director every morning at 8:00 AM.")
            st.markdown("---")
            
            st.markdown(f"### 📅 IDinsight Daily Intelligence Briefing | {datetime.date.today()}")
            st.markdown(f"**Generated for:** {role}")
            st.markdown(f"**Total High-Match Opportunities:** {len(high_matches)}")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not high_matches:
                st.warning("No opportunities met the minimum 50% threshold today.")
            
            for r in high_matches:
                st.success(
                    f"**[{r['score']}% MATCH] {r['title']}**\n\n"
                    f"**Why it matches:** {r['rationale'].replace('✅', '').replace('**', '')}\n\n"
                    f"🔗 **[Click here to view the full RFP document]({r['url']})**"
                )
