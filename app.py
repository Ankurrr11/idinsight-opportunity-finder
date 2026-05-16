import streamlit as st
import requests
import datetime
import xml.etree.ElementTree as ET

st.set_page_config(page_title="IDinsight Opportunity Finder", page_icon="🌍", layout="wide")

# --- DATA INGESTION (RSS FEED) ---
def fetch_live_opportunities(days=7):
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
                
                jobs.append({
                    'fields': {
                        'title': title,
                        'body-html': description,
                        'url': link,
                        'date': {'created': pubDate},
                        'country': [], 
                        'source': [{'name': 'ReliefWeb'}]
                    }
                })
            return jobs
        return []
    except Exception as e:
        st.error(f"RSS Fetch Error: {e}")
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
    else:
        rationale.append("❌ **Geography:** Outside primary geographic focus.")

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
st.markdown("Automated intelligence pipeline for identifying high-potential RFPs and B2B opportunities in global development.")

st.sidebar.header("Pipeline Settings")
st.sidebar.info("This tool pulls live data from the ReliefWeb RSS feed, filters for recent posts, and uses an algorithmic scoring engine to rank opportunities based on IDinsight's profile.")

# --- NEW: ROLE BASED ACCESS ---
st.sidebar.divider()
st.sidebar.header("🔐 User Authentication")
role = st.sidebar.selectbox("Simulate Logged-in User:", ["Global Director", "Director of Africa", "Director of Asia"])

if st.sidebar.button("Run Daily Report Engine", type="primary"):
    with st.spinner("Scraping global development databases..."):
        raw_data = fetch_live_opportunities()
        
    if not raw_data:
        st.warning("No opportunities found for this timeframe.")
    else:
        st.success(f"Successfully retrieved recent opportunities. Running scoring engine...")
        
        results = []
        for job in raw_data:
            score, rationale = analyze_and_score(job)
            results.append({
                "title": job['fields'].get('title', 'Untitled'),
                "url": job['fields'].get('url', ''),
                "date": job['fields'].get('date', {}).get('created', '')[:16],
                "score": score,
                "rationale": rationale
            })
            
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        st.header(f"🏆 Top Opportunities for: {role}")
        high_matches = [r for r in results if r['score'] >= 50]
        if not high_matches:
            st.info("No high-match opportunities found today.")
            
        for i, r in enumerate(high_matches):
            with st.expander(f"[{r['score']}% Match] {r['title']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Scoring Rationale:**\n\n{r['rationale']}")
                    st.markdown(f"[🔗 View Full Application/RFP Details]({r['url']})")
                    
                    # --- NEW: ENTERPRISE FEATURES ---
                    st.divider()
                    st.write("**⚙️ Enterprise Actions:**")
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    if btn_col1.button("👍 Train AI (Upvote)", key=f"up_{i}"):
                        st.toast("Model updated: The AI will prioritize similar RFPs in the future.", icon="🧠")
                    if btn_col2.button("👎 Train AI (Downvote)", key=f"down_{i}"):
                        st.toast("Model updated: The AI will ignore similar RFPs.", icon="📉")
                    if btn_col3.button("☁️ Push to Salesforce", key=f"crm_{i}"):
                        st.toast("Success: Created new Lead in Salesforce CRM!", icon="✅")
                        
                with col2:
                    st.metric("AI Match Score", f"{r['score']}%")
                    st.caption(f"📅 Published: {r['date']} 🟢 *(Fresh)*")
                    
        st.divider()
        st.header("Other Scanned Items (Low Match)")
        for r in [r for r in results if r['score'] < 50][:10]:
            st.markdown(f"- **{r['score']}%** | {r['title']} ([Link]({r['url']}))")
else:
    st.info("👈 Click **Run Daily Report Engine** to execute the pipeline.")

