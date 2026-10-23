import os
from dashboard.review import render_review_page
from pathlib import Path
from dashboard.monitoring import render_monitoring_page
from datetime import datetime
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
API_URL = os.getenv('RESOLVEOPS_API_URL', 'http://127.0.0.1:8000').rstrip('/')
API_KEY = os.getenv('RESOLVEOPS_API_KEY', '')

st.set_page_config(page_title='ResolveOps | Command Center', page_icon='🛡️', layout='wide', initial_sidebar_state='expanded')

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root {color-scheme: dark;}
html,body,[class*="css"],.stApp {font-family:'DM Sans',sans-serif;}
.stApp {background: radial-gradient(ellipse 72% 40% at 55% -15%, rgba(55,101,225,.19), transparent 80%), #080d19; color:#e9efff;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#101b30,#0a1222); border-right:1px solid #24334f;}
[data-testid="stSidebar"] * {color:#e9efff;}
.block-container {padding-top:2rem; padding-bottom:4rem; max-width:1480px;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif;letter-spacing:-.035em;}
h1 {font-size:2.35rem !important;}
h3 {font-size:1.15rem !important;}
[data-testid="stMetric"] {background:linear-gradient(145deg,#17253e,#111b2f); border:1px solid #2b3e60; border-radius:18px; padding:20px 22px; box-shadow:0 12px 34px rgba(0,0,0,.14); animation:rise .65s ease both; transition:transform .22s ease, border-color .22s ease, box-shadow .22s ease;}
[data-testid="stMetric"]:hover {transform:translateY(-5px);border-color:#5b85e7;box-shadow:0 18px 40px rgba(37,93,209,.2);}
[data-testid="stMetricLabel"] {color:#a9b9d7;}
[data-testid="stMetricValue"] {color:#f5f8ff; font-family:'Space Grotesk',sans-serif;}
[data-testid="stVerticalBlockBorderWrapper"] > div {border-color:#283a58 !important; border-radius:18px !important;}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {border-radius:16px; overflow:hidden;}
.stButton > button {background:linear-gradient(120deg,#3465e7,#5488f9);color:white;border:1px solid #6a96ff;border-radius:11px;font-weight:700;transition:transform .2s ease,box-shadow .2s ease;}
.stButton > button:hover {transform:translateY(-2px);box-shadow:0 8px 26px rgba(68,111,241,.3);color:white;border-color:#9ab7ff;}
.stTextInput input,[data-baseweb="select"] > div {border-radius:10px !important;}
.hero {position:relative;overflow:hidden;background:linear-gradient(110deg,rgba(29,51,91,.96),rgba(14,27,51,.94));border:1px solid #35517b;border-radius:24px;padding:30px 34px;margin-bottom:25px;animation:rise .55s ease both;}
.hero:after {content:'';position:absolute;right:-70px;top:-130px;width:390px;height:390px;background:radial-gradient(circle,rgba(70,117,255,.28),transparent 70%);pointer-events:none;}
.eyebrow {color:#88afff;font-size:.75rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase;margin-bottom:8px;}
.hero-title {font-family:'Space Grotesk',sans-serif;font-size:2.4rem;letter-spacing:-.045em;font-weight:700;line-height:1.15;color:#fff;}
.hero-sub {color:#b4c4df;margin-top:12px;font-size:.98rem;max-width:730px;}
.pill {display:inline-block;border:1px solid #3c6b68;background:#143b3d;color:#8df0c9;padding:7px 12px;border-radius:999px;font-size:.78rem;font-weight:800;margin-top:16px;}
.section-heading {color:#e9efff;font-family:'Space Grotesk',sans-serif;font-size:1.3rem;font-weight:700;margin:12px 0 12px;}
.muted {color:#9aaccb;font-size:.88rem;}
@keyframes rise {from {opacity:0;transform:translateY(13px)}to{opacity:1;transform:translateY(0)}}
@media (prefers-reduced-motion:reduce) {* {animation:none !important;transition:none !important;}}
@media (max-width:700px) {.hero {padding:22px}.hero-title{font-size:1.8rem}.block-container{padding-top:1rem}}
</style>''', unsafe_allow_html=True)

@st.cache_data(ttl=15, show_spinner=False)
def fetch_incidents():
    if not API_KEY:
        raise ValueError('RESOLVEOPS_API_KEY is missing from the project .env file.')
    response = requests.get(f'{API_URL}/incidents', headers={'X-API-Key':API_KEY,'Accept':'application/json'}, timeout=12)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, list):
        raise ValueError('Expected a list of incidents from FastAPI.')
    return result

with st.sidebar:
    st.markdown('## 🛡️ ResolveOps')
    st.caption('INTELLIGENT INCIDENT OPERATIONS')
    st.divider()
    page = st.radio(
    'WORKSPACE',
    ['Overview', 'Incident Registry', 'Analytics', 'Human Review', 'SLA & Notifications',],
    label_visibility='visible'
    )
    st.divider()
    st.markdown('**SYSTEM INTEGRATIONS**')
    st.caption('🟢 FastAPI · Local backend')
    st.caption('🔵 UiPath · Automation workflow')
    st.caption('🟣 SQLite · Incident storage')
    st.write('')
    if st.button('↻  Refresh live data', use_container_width=True):
        fetch_incidents.clear()
        st.rerun()
    st.caption('Data refresh cache: 15 seconds')

st.markdown('''<div class="hero"><div class="eyebrow">ResolveOps / Operations Workspace</div><div class="hero-title">Incident Command Center</div><div class="hero-sub">A unified view of incident intake, AI-driven triage, team routing and service response. Real data. Clear decisions.</div><span class="pill">● SYSTEM CONNECTED</span></div>''',unsafe_allow_html=True)

try:
    incidents = fetch_incidents()
except requests.exceptions.RequestException as exc:
    st.error(f'Cannot retrieve incidents from {API_URL}. Confirm FastAPI is running. Details: {exc}')
    st.stop()
except (ValueError, TypeError) as exc:
    st.error(str(exc))
    st.stop()

if not incidents:
    st.info('No incidents yet. Submit one through FastAPI to populate this dashboard.')
    st.stop()

df = pd.DataFrame(incidents)
for field in ['id','title','description','category','priority','status','assigned_team','created_at','sla_deadline']:
    if field not in df.columns:
        df[field] = None
for field in ['category','priority','status','assigned_team']:
    df[field] = df[field].fillna('Unassigned').replace('', 'Unassigned').astype(str)
for field in ['title','description']:
    df[field] = df[field].fillna('').astype(str)

total = len(df)
pending = int(df['status'].str.casefold().eq('pending').sum())
urgent = int(df['priority'].str.casefold().isin(['high','critical']).sum())
review = int(df['status'].str.casefold().eq('review required').sum())

st.markdown('<div class="section-heading">Operations at a glance</div>',unsafe_allow_html=True)
a,b,c,d = st.columns(4)
a.metric('TOTAL INCIDENTS', total, help='All incident records in SQLite')
b.metric('PENDING AUTOMATION', pending, help='Awaiting UiPath processing')
c.metric('HIGH / CRITICAL', urgent, help='Tickets marked High or Critical')
d.metric('HUMAN REVIEW', review, help='Tickets marked Review Required')
st.write('')

if page in ['Overview','Incident Registry']:
    st.markdown('<div class="section-heading">Incident registry</div>',unsafe_allow_html=True)
    f1,f2,f3 = st.columns(3)
    with f1:
        status = st.selectbox('Status', ['All']+sorted(df['status'].unique().tolist()))
    with f2:
        priority = st.selectbox('Priority', ['All']+sorted(df['priority'].unique().tolist()))
    with f3:
        category = st.selectbox('Category', ['All']+sorted(df['category'].unique().tolist()))
    search = st.text_input('Quick search', placeholder='Search ID, title or description…')
    filtered = df.copy()
    if status!='All': filtered=filtered[filtered['status']==status]
    if priority!='All': filtered=filtered[filtered['priority']==priority]
    if category!='All': filtered=filtered[filtered['category']==category]
    if search.strip():
        s=search.strip().casefold()
        filtered=filtered[filtered['id'].astype(str).str.contains(s,regex=False) | filtered['title'].str.casefold().str.contains(s,regex=False) | filtered['description'].str.casefold().str.contains(s,regex=False)]
    shown=['id','title','category','priority','status','assigned_team']
    if df['sla_deadline'].notna().any(): shown.append('sla_deadline')
    st.dataframe(filtered.sort_values('id',ascending=False)[shown],use_container_width=True,hide_index=True,height=min(470,100+len(filtered)*37),column_config={'id':st.column_config.NumberColumn('ID',format='#%d'),'title':'Incident','category':'Category','priority':'Priority','status':'Status','assigned_team':'Assigned team','sla_deadline':'SLA deadline'})
    st.caption(f'{len(filtered)} matching incidents · {total} total records')

if page in ['Overview','Analytics']:
    st.markdown('<div class="section-heading">Operational intelligence</div>',unsafe_allow_html=True)
    chart_a,chart_b=st.columns(2)
    with chart_a:
        category_counts=df['category'].value_counts().reset_index()
        category_counts.columns=['Category','Incidents']
        fig=px.bar(category_counts,x='Incidents',y='Category',orientation='h',title='Incidents by category',color='Incidents',color_continuous_scale=['#274678','#4786f7','#8db7ff'])
        fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',coloraxis_showscale=False,margin=dict(l=8,r=16,t=55,b=12),height=330,font=dict(family='DM Sans',color='#c7d5ed'),title_font=dict(size=17),yaxis=dict(categoryorder='total ascending'),xaxis=dict(gridcolor='#233551'))
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    with chart_b:
        counts=df['priority'].value_counts().reset_index()
        counts.columns=['Priority','Incidents']
        fig=px.pie(counts,names='Priority',values='Incidents',hole=.64,title='Priority distribution',color='Priority',color_discrete_map={'Critical':'#f25d75','High':'#ffad63','Medium':'#649cff','Low':'#58d9b4','Unassigned':'#60718c'})
        fig.update_traces(textposition='outside',textinfo='percent+label',marker=dict(line=dict(color='#10182a',width=3)))
        fig.update_layout(template='plotly_dark',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=8,r=8,t=55,b=10),height=330,font=dict(family='DM Sans',color='#c7d5ed'),title_font=dict(size=17),showlegend=False)
        st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

if page == "Human Review":
    render_review_page()
    st.stop()
if page == "SLA & Notifications":
        render_monitoring_page(
            API_URL,
            API_KEY,
            incidents,
        )
        st.stop()
st.markdown('<div class="section-heading">Incident inspector</div>',unsafe_allow_html=True)
options=sorted([int(x) for x in df['id'].dropna().tolist()],reverse=True)
selected_id=st.selectbox('Inspect incident',options,format_func=lambda i: f'#{i}  ·  {df.loc[df["id"]==i,"title"].iloc[0][:75]}')
record=next(x for x in incidents if int(x.get('id'))==selected_id)
with st.container(border=True):
    left,right=st.columns([1.4,1])
    with left:
        st.markdown(f'### #{selected_id} — {record.get("title", "Untitled")}')
        st.caption('INCIDENT DESCRIPTION')
        st.write(record.get('description') or 'No description provided.')
    with right:
        st.markdown('#### Triage details')
        st.write('**Status:**',record.get('status') or 'Unassigned')
        st.write('**Category:**',record.get('category') or 'Unassigned')
        st.write('**Priority:**',record.get('priority') or 'Unassigned')
        st.write('**Team:**',record.get('assigned_team') or 'Unassigned')
        if record.get('sla_deadline'): st.write('**SLA deadline:**',record['sla_deadline'])

st.divider()
st.caption('ResolveOps · AI-assisted triage · UiPath automation · FastAPI · SQLite  |  Live API-backed dashboard')

