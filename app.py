import streamlit as st
import requests
import datetime
import urllib.parse
import xml.etree.ElementTree as ET

st.set_page_config(page_title="IDinsight Opportunity Finder", page_icon="🌍", layout="wide")

# --- DATA INGESTION (RSS FEED) ---
def fetch_live_opportunities(days=7):
    # ReliefWeb v1 API was decommissioned, so we use their public RSS feed instead!
    # This guarantees we get the absolute latest live data without needing API keys.
    url = "https://reliefweb.int/jobs/rss.xml"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            jobs = []
            # Parse the RSS XML items
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
                        'source': [{'name': 'ReliefWeb Source'}]
                    }
                })
            return jobs
        return []
    except Exception as e:
        st.error(f"RSS Fetch Error: {e}")
        return []

# --- AI / FILTERING ENGINE ---
def analyze_and_score(job_data):
    # This acts as our "AI" filtering engine for the prototype.
    # In a full production app, this function would pass the text to GPT-4 or Gemini via API.
    title = job_data['fields'].get('title', '').lower()
    body = job_data['fields'].get('body-html', '').lower()
    country = [c.get('name', '').lower() for c in job_data['fields'].get('country', [])]
    
    score = 0
    rationale = []
    
    # 1. Geographic Presence Match (Africa/Asia)
    target_regions = ['africa', 'asia', 'kenya', 'india', 'senegal', 'zambia', 'philippines', 'nigeria', 'uganda', 'malawi', 'morocco']
    geo_match = any(region in title or region in body for region in target_regions)
    country_match = any(region in c for region in target_regions for c in country)
    
    if geo_match or country_match:
        score += 40
        rationale.append("✅ **Geography:** Strong alignment with target regions (Africa/Asia).")
    else:
        rationale.append("❌ **Geography:** Outside primary geographic focus.")

    # 2. Sector / Service Match
    if any(k in title or k in body for k in ['impact evaluation', 'rct', 'randomized control']):
        score += 35
        rationale.append("✅ **Services:** High alignment with Impact Evaluation / RCT.")
    elif any(k in title or k in body for k in ['data analytics', 'machine learning', 'survey', 'research']):
        score += 25
        rationale.append("✅ **Services:** Strong alignment with Data & Tech Services.")
        
    # 3. Target client type (Foundation, Gov, NGO)
    if any(k in title or k in body for k in ['consultancy', 'rfp', 'request for proposal', 'bids']):
        score += 25
        rationale.append("✅ **Type:** Confirmed B2B / Consultancy Opportunity.")
        
    return score, " ".join(rationale)

# --- UI ---
st.title("🌍 IDinsight Client Opportunity Finder")
st.markdown("Automated intelligence pipeline for identifying high-potential RFPs and B2B opportunities in global development.")

st.sidebar.header("Pipeline Settings")
st.sidebar.info("This tool pulls live data from the ReliefWeb API (a global development aggregator), filters for recent posts, and uses an algorithmic scoring engine to rank opportunities based on IDinsight's profile.")

days_back = st.sidebar.slider("Look back (Days) - 'Freshness'", 1, 14, 7)

if st.sidebar.button("Run Daily Report Engine", type="primary"):
    with st.spinner(f"Scraping global development databases for the last {days_back} days..."):
        raw_data = fetch_live_opportunities(days_back)
        
    if not raw_data:
        st.warning("No opportunities found for this timeframe. Try expanding the Look back days.")
    else:
        st.success(f"Successfully retrieved {len(raw_data)} recent opportunities. Running scoring engine...")
        
        results = []
        for job in raw_data:
            score, rationale = analyze_and_score(job)
            source_names = [source.get('name', 'Unknown') for source in job['fields'].get('source', [])]
            results.append({
                "title": job['fields'].get('title', 'Untitled'),
                "url": job['fields'].get('url', ''),
                "date": job['fields'].get('date', {}).get('created', '')[:10],
                "score": score,
                "rationale": rationale,
                "organization": source_names
            })
            
        # Sort by best match
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        st.header("🏆 Top Opportunities for IDinsight")
        
        high_matches = [r for r in results if r['score'] >= 50]
        if not high_matches:
            st.info("No high-match opportunities found today.")
            
        for r in high_matches:
            with st.expander(f"[{r['score']}% Match] {r['title']} - {', '.join(r['organization'])}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Posted By:** {', '.join(r['organization'])}")
                    st.markdown(f"**Scoring Rationale:**\n\n{r['rationale']}")
                    st.markdown(f"[🔗 View Full Application/RFP Details]({r['url']})")
                with col2:
                    st.metric("AI Match Score", f"{r['score']}%")
                    st.caption(f"📅 Published: {r['date']} 🟢 *(Fresh)*")
                    
        st.divider()
        st.header("Other Scanned Items (Low Match)")
        low_matches = [r for r in results if r['score'] < 50]
        for r in low_matches:
            st.markdown(f"- **{r['score']}%** | {r['title']} ([Link]({r['url']}))")

else:
    st.info("👈 Click **Run Daily Report Engine** to execute the pipeline and fetch today's opportunities.")
