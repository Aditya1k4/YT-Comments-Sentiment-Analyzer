import streamlit as st
import os
from Senti import (
    extract_video_id, analyze_sentiment,
    bar_chart, plot_sentiment, plot_emotions, EMOTION_META
)
from YoutubeCommentScrapper import (
    save_video_comments_to_csv, get_channel_info,
    youtube, get_channel_id, get_video_stats
)
import streamlit as st

is_mobile = st.query_params.get("mobile", "0") == "1"

# ── Page config ────────────────────────────────────────────────────────────────
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = True

st.set_page_config(
    page_title='YT Sentiment Insights',
    page_icon='LOGO.png',
    layout='wide',
    initial_sidebar_state="collapsed" if is_mobile else (
        "expanded" if st.session_state.show_sidebar else "collapsed"
    )
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap');

#MainMenu, footer, header { visibility: hidden; }

[data-testid="stAppViewContainer"] {
    background-color: #0d0d1a;
    background-image:
        repeating-linear-gradient(
            -30deg,
            transparent,
            transparent 120px,
            rgba(99,102,241,0.03) 120px,
            rgba(99,102,241,0.03) 121px
        );
    position: relative;
}

.watermark-bg {
    position: fixed;
    inset: 0;
    display: flex;
    flex-wrap: wrap;
    align-content: flex-start;
    gap: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
    opacity: 0.04;
}
.watermark-bg span {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.2rem;
    color: #818cf8;
    white-space: nowrap;
    padding: 0.4rem 1.5rem;
    letter-spacing: 0.12em;
}

[data-testid="stSidebar"],
[data-testid="block-container"] { position: relative; z-index: 1; }

[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f0f2a 0%, #1a1040 100%);
    border-right: 1px solid rgba(129,140,248,0.15);
}
[data-testid="stSidebar"] * { color: #c7d2fe !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(129,140,248,0.3) !important;
    border-radius: 10px !important;
    color: #e0e7ff !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 0.1em;
    color: #818cf8 !important;
}

h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 0.08em; }
p, span, div, label { font-family: 'DM Sans', sans-serif !important; }

.metric-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.08));
    border: 1px solid rgba(129,140,248,0.2);
    border-radius: 16px;
    padding: 1.4rem 1rem;
    text-align: center;
    backdrop-filter: blur(8px);
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(99,102,241,0.2); }
.metric-card .label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #818cf8;
    margin-bottom: 0.5rem;
}
.metric-card .value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.4rem;
    color: #e0e7ff;
    letter-spacing: 0.05em;
}

.emotion-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}
.emotion-tile {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.1rem 0.8rem;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
}
.emotion-tile:hover { transform: scale(1.05); }
.emotion-tile .e-icon { font-size: 2rem; }
.emotion-tile .e-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 0.1em;
    margin: 0.3rem 0 0.1rem;
}
.emotion-tile .e-count {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    color: #a0aec0;
}

.section-pill {
    display: inline-block;
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    color: #fff !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem;
    letter-spacing: 0.15em;
    padding: 0.35rem 1.2rem;
    border-radius: 100px;
    margin-bottom: 1.2rem;
}

[data-testid="stDownloadButton"] button {
    background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.2rem !important;
    transition: opacity 0.2s !important;
}
[data-testid="stDownloadButton"] button:hover { opacity: 0.85 !important; }

.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #6366f1, transparent);
    margin: 2rem 0;
}

.channel-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    letter-spacing: 0.06em;
    color: #e0e7ff;
    line-height: 1.1;
    margin-top: 0.5rem;
}

.insight-badge {
    display: inline-block;
    padding: 0.25rem 0.8rem;
    border-radius: 100px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    margin: 0.2rem;
}

textarea { background: rgba(255,255,255,0.05) !important; color: #c7d2fe !important; border-radius: 10px !important; }
body, p, span { color: #c7d2fe; }
</style>
""", unsafe_allow_html=True)

# ── Watermark ──────────────────────────────────────────────────────────────────
watermark_html = "<div class='watermark-bg'>" + ("<span>YOUR INSIGHTS</span>" * 120) + "</div>"
st.markdown(watermark_html, unsafe_allow_html=True)

#hide menu

st.markdown("""
<style>
@media (max-width: 768px) {
    button[data-testid="baseButton-secondary"] {
        display: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ── Menu Button (Desktop ONLY) ────────────────────────
if not is_mobile:
    col1, col2 = st.columns([0.05, 0.95])

    with col1:
        if st.button("☰"):
            st.session_state.show_sidebar = not st.session_state.show_sidebar
            st.rerun()

# ── Sidebar (Always On - Controlled by page_config) ─────────
if "youtube_link" not in st.session_state:
    st.session_state.youtube_link = ""

with st.sidebar:
    st.markdown("<h1>🎬 YT Sentiment</h1>", unsafe_allow_html=True)
    st.markdown("<h2>Paste a YouTube Link</h2>", unsafe_allow_html=True)

    st.session_state.youtube_link = st.text_input(
        "YouTube URL",
        value=st.session_state.youtube_link,
        placeholder="https://youtube.com/watch?v=...",
        label_visibility="collapsed"
    )

youtube_link = st.session_state.youtube_link
    
directory_path = os.getcwd()


def delete_stale_csvs(directory, keep_id):
    for fn in os.listdir(directory):
        if fn.endswith('.csv') and fn != f'{keep_id}.csv':
            os.remove(os.path.join(directory, fn))


def _card(label, value, col):
    col.markdown(
        f"<div class='metric-card'>"
        f"<div class='label'>{label}</div>"
        f"<div class='value'>{value}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ── Main ───────────────────────────────────────────────────────────────────────
if youtube_link:
    video_id = extract_video_id(youtube_link)
    if not video_id:
        st.error("⚠️ Invalid YouTube link — please check and try again.")
        st.stop()

    channel_id = get_channel_id(video_id)

    with st.spinner("Fetching comments & crunching sentiments…"):
        csv_file = save_video_comments_to_csv(video_id)
        delete_stale_csvs(directory_path, video_id)
        results = analyze_sentiment(csv_file)
        channel_info = get_channel_info(youtube, channel_id)
        stats = get_video_stats(video_id)

    # ── Sidebar extras ─────────────────────────────────────────────────────────
    st.sidebar.markdown(f"**Video ID:** `{video_id}`")
    st.sidebar.markdown("✅ Comments saved to CSV")
    with open(csv_file, 'rb') as f:
        st.sidebar.download_button(
            "⬇ Download Comments CSV", f.read(),
            file_name=f"{video_id}.csv", mime="text/csv"
        )

    # ── Channel header ─────────────────────────────────────────────────────────
    st.markdown("<div class='section-pill'>Channel Info</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 3])
    with c1:
        st.image(channel_info['channel_logo_url'], width=190)
    with c2:
        ch_title = channel_info['channel_title']
        st.markdown(f"<div class='channel-name'>{ch_title}</div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        _card("Total Videos", channel_info['video_count'], m1)
        _card("Founded", channel_info['channel_created_date'][:10], m2)
        _card("Subscribers", channel_info['subscriber_count'], m3)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Video stats ────────────────────────────────────────────────────────────
    st.markdown("<div class='section-pill'>Video Stats</div>", unsafe_allow_html=True)
    v1, v2, v3 = st.columns(3)
    _card("👁 Views", stats.get('viewCount', 'N/A'), v1)
    _card("👍 Likes", stats.get('likeCount', 'N/A'), v2)
    _card("💬 Comments", stats.get('commentCount', 'N/A'), v3)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Embedded video ─────────────────────────────────────────────────────────
    _, vid_col, _ = st.columns([1, 6, 1])
    vid_col.video(youtube_link)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Sentiment summary ──────────────────────────────────────────────────────
    st.markdown("<div class='section-pill'>Sentiment Overview</div>", unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    _card("✅ Positive", results['num_positive'], s1)
    _card("❌ Negative", results['num_negative'], s2)
    _card("😐 Neutral", results['num_neutral'], s3)
    _card("📝 Total", results['total'], s4)

    bar_chart(csv_file)
    plot_sentiment(csv_file)

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Emotion insights ───────────────────────────────────────────────────────
    st.markdown("<div class='section-pill'>🎭 Emotion Insights</div>", unsafe_allow_html=True)

    ec = results['emotion_counts']
    total = results['total'] or 1

    tiles_html = "<div class='emotion-grid'>"
    for emotion, meta in EMOTION_META.items():
        count = ec[emotion]
        pct = round(count / total * 100, 1)
        color = meta['color']
        icon = meta['icon']
        tiles_html += (
            f"<div class='emotion-tile' style='border-color:{color}33;'>"
            f"<div class='e-icon'>{icon}</div>"
            f"<div class='e-name' style='color:{color}'>{emotion.upper()}</div>"
            f"<div class='e-count'>{count} comments · {pct}%</div>"
            f"</div>"
        )
    tiles_html += "</div>"
    st.markdown(tiles_html, unsafe_allow_html=True)

    plot_emotions(csv_file)

    # ── Dominant emotion callout ───────────────────────────────────────────────
    dom_emotion = max(ec, key=ec.get)
    dom_meta = EMOTION_META[dom_emotion]
    dom_pct = round(ec[dom_emotion] / total * 100, 1)
    dom_color = dom_meta['color']
    dom_icon = dom_meta['icon']

    insight_msgs = {
        'funny':        f"The audience finds this content hilarious! {dom_pct}% of comments express amusement.",
        'lovely':       f"This video is showered with love — {dom_pct}% of comments radiate positivity and admiration.",
        'angry':        f"Watch out! {dom_pct}% of comments carry frustration or anger. Check for controversy.",
        'advice':       f"The community is engaged and constructive — {dom_pct}% of comments offer suggestions or tips.",
        'sad':          f"This video resonates emotionally; {dom_pct}% of comments express sadness or empathy.",
        'motivational': f"Inspiring! {dom_pct}% of comments are uplifting and encouraging.",
        'spam':         f"Caution — {dom_pct}% of comments appear to be spam or self-promotion.",
    }

    st.markdown(
        f"""<div style='background:linear-gradient(135deg,{dom_color}22,{dom_color}08);
            border:1px solid {dom_color}55; border-radius:16px; padding:1.4rem 1.6rem; margin-top:1rem;'>
            <span style='font-size:2rem'>{dom_icon}</span>
            <span style='font-family:Bebas Neue,sans-serif;font-size:1.4rem;color:{dom_color};
            letter-spacing:0.1em;margin-left:0.6rem;'>DOMINANT EMOTION: {dom_emotion.upper()}</span>
            <p style='margin:0.6rem 0 0;font-family:DM Sans,sans-serif;color:#c7d2fe;font-size:1rem;'>
            {insight_msgs[dom_emotion]}</p></div>""",
        unsafe_allow_html=True
    )

    st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

    # ── Channel description ────────────────────────────────────────────────────
    st.markdown("<div class='section-pill'>About the Channel</div>", unsafe_allow_html=True)
    ch_desc = channel_info['channel_description']
    st.markdown(
        f"<p style='color:#94a3b8;line-height:1.8;'>{ch_desc}</p>",
        unsafe_allow_html=True
    )

else:
    # ── Landing state ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center;padding:6rem 2rem;'>
        <div style='font-family:Bebas Neue,sans-serif;font-size:5rem;letter-spacing:0.08em;
             background:linear-gradient(135deg,#818cf8,#c084fc);-webkit-background-clip:text;
             -webkit-text-fill-color:transparent;line-height:1.05;'>
            YOUR INSIGHTS<br>AWAIT
        </div>
        <p style='font-family:DM Sans,sans-serif;color:#64748b;font-size:1.15rem;
           margin-top:1.5rem;max-width:480px;margin-left:auto;margin-right:auto;'>
            Paste a YouTube link in the sidebar to analyse comments across
            <strong style='color:#818cf8;'>7 emotions</strong> — funny, lovely, angry,
            advice, sad, motivational &amp; spam.
        </p>
        <div style='margin-top:3rem;display:flex;justify-content:center;flex-wrap:wrap;gap:0.8rem;'>
            <span class='insight-badge' style='background:#FFD93D22;color:#FFD93D;border:1px solid #FFD93D44;'>😂 Funny</span>
            <span class='insight-badge' style='background:#FF6B9D22;color:#FF6B9D;border:1px solid #FF6B9D44;'>❤️ Lovely</span>
            <span class='insight-badge' style='background:#FF474722;color:#FF4747;border:1px solid #FF474744;'>😡 Angry</span>
            <span class='insight-badge' style='background:#4FC3F722;color:#4FC3F7;border:1px solid #4FC3F744;'>💡 Advice</span>
            <span class='insight-badge' style='background:#7E9CC722;color:#7E9CC7;border:1px solid #7E9CC744;'>😢 Sad</span>
            <span class='insight-badge' style='background:#69DB7C22;color:#69DB7C;border:1px solid #69DB7C44;'>💪 Motivational</span>
            <span class='insight-badge' style='background:#B0B0B022;color:#B0B0B0;border:1px solid #B0B0B044;'>🚫 Spam</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
