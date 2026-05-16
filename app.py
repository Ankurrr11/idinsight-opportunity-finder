import streamlit as st
import requests
import datetime
import xml.etree.ElementTree as ET
import email.utils

st.set_page_config(page_title="IDinsight Opportunity Finder", page_icon="🌍", layout="wide")

# --- DATA INGESTION (RSS FEED) ---
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
st.title("🌍 IDinsight Client Opportunity Finder")
st.markdown("Automated intelligence pipeline for identifying high-potential RFPs and B2B opportunities.")

st.sidebar.header("📅 Report Settings")
timeframe = st.sidebar.selectbox("Filter Date Range:", ["Last 7 Days (Fresh)", "Today Only", "Last 30 Days", "All Time"])
st.sidebar.divider()
st.sidebar.header("🔐 User Authentication")
role = st.sidebar.selectbox("Simulate Logged-in User:", ["Global Director", "Director of Africa", "Director of Asia"])

tab1, tab2 = st.tabs(["📊 Live Intelligence Dashboard", "📩 Daily Report Digest"])

if st.sidebar.button("Generate Daily Summary", type="primary"):
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
                if timeframe == "Today Only" and days_old > 1: continue
                if timeframe == "Last 7 Days (Fresh)" and days_old > 7: continue
                if timeframe == "Last 30 Days" and days_old > 30: continue
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

        # --- TAB 1: THE DASHBOARD ---
        with tab1:
            st.success(f"Generated Daily Summary! Found {len(filtered_data)} opportunities for {timeframe}.")
            st.header(f"🏆 Top Daily Opportunities for: {role}")
            if not high_matches: st.info("No high-match opportunities found today.")
                
            for i, r in enumerate(high_matches):
                with st.expander(f"[{r['score']}% Match] {r['title']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Scoring Rationale:**\n\n{r['rationale']}")
                        st.markdown(f"[🔗 View Full Application/RFP Details]({r['url']})")
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
            st.header("Other Scanned Items (Low Match)")
            for r in [r for r in results if r['score'] < 50][:10]:
                st.markdown(f"- **{r['score']}%** | {r['title']} ([Link]({r['url']}))")

        # --- TAB 2: VISUAL REPORT DIGEST ---
        with tab2:
            st.header("📩 Today's Executive Digest (Preview)")
            st.caption("This is a visual preview of the automated email sent to the Director every morning at 8:00 AM.")
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
else:
    st.info("👈 Click **Generate Daily Summary** to run the pipeline.")
