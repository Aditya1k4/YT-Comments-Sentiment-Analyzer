import csv
import re
import pandas as pd
import nltk
nltk.download('vader_lexicon', quiet=True)
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict
import streamlit as st

# ── Emotion keyword maps ───────────────────────────────────────────────────────
EMOTION_KEYWORDS = {
    'funny': [
        'lol', 'lmao', 'haha', 'hehe', 'hilarious', 'funny', 'comedy', 'joke',
        'rofl', 'xd', '😂', '🤣', 'laughing', 'cringe', 'meme', 'humor', 'witty',
        'sarcastic', 'ironic', 'absurd', 'ridiculous', 'silly', 'goofy'
    ],
    'lovely': [
        'love', 'lovely', 'beautiful', 'amazing', 'wonderful', 'adorable', 'cute',
        'sweet', 'heart', '❤️', '🥰', '😍', 'gorgeous', 'precious', 'charming',
        'delightful', 'fantastic', 'brilliant', 'perfect', 'favorite', 'obsessed'
    ],
    'angry': [
        'hate', 'angry', 'furious', 'disgusting', 'awful', 'terrible', 'worst',
        'stupid', 'idiot', 'trash', 'garbage', 'pathetic', 'useless', 'waste',
        '😡', '🤬', 'disgusted', 'annoying', 'annoyed', 'infuriating', 'outrage',
        'scam', 'fraud', 'liar', 'fake', 'clickbait', 'clickbaited'
    ],
    'advice': [
        'should', 'recommend', 'suggest', 'advice', 'tip', 'try', 'better if',
        'you need', 'you must', 'please', 'improve', 'consider', 'maybe',
        'perhaps', 'would be nice', 'next time', 'instead', 'feedback',
        'constructive', 'criticism', 'suggestion', 'idea'
    ],
    'sad': [
        'sad', 'cry', 'crying', 'tears', 'heartbroken', 'miss', 'lonely',
        'depressed', 'depression', 'grief', 'pain', 'hurt', 'broken', 'lost',
        '😢', '😭', '💔', 'unfortunate', 'tragedy', 'tragic', 'regret',
        'sorry', 'disappointed', 'disappointment', 'hopeless', 'helpless'
    ],
    'motivational': [
        'inspire', 'inspired', 'motivation', 'motivated', 'keep going', 'never give up',
        'proud', 'strength', 'courage', 'believe', 'dream', 'achieve', 'success',
        'winner', 'champion', 'legend', 'hero', 'powerful', 'amazing job',
        'well done', 'great work', 'incredible', 'outstanding', 'applaud',
        'respect', '🙌', '💪', '🔥', '⭐', 'god bless', 'blessed'
    ],
    'spam': [
        'subscribe', 'sub4sub', 'follow me', 'check out my', 'visit my',
        'free', 'giveaway', 'click here', 'link in bio', 'dm me', 'promo',
        'discount', 'coupon', 'buy now', 'limited offer', 'earn money',
        'make money', 'work from home', 'investment', 'crypto', 'bitcoin',
        'http', 'www.', '.com', 'instagram', 'telegram', '👇', '🔗'
    ],
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_video_id(youtube_link: str):
    pattern = r"^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, youtube_link)
    return match.group(1) if match else None


def _detect_emotion(text: str) -> str:
    """Return the dominant emotion label for a comment string."""
    lower = text.lower()
    scores = {emotion: 0 for emotion in EMOTION_KEYWORDS}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[emotion] += 1
    best = max(scores, key=scores.get)
    # Fall back to VADER-based positive/negative/neutral when no keyword matched
    if scores[best] == 0:
        sid = SentimentIntensityAnalyzer()
        compound = sid.polarity_scores(text)['compound']
        if compound > 0.05:
            return 'lovely'
        elif compound < -0.05:
            return 'angry'
        else:
            return 'motivational'   # neutral → bucket into motivational
    return best


# ── Core analysis ──────────────────────────────────────────────────────────────

def analyze_sentiment(csv_file: str) -> Dict:
    sid = SentimentIntensityAnalyzer()

    comments = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            comments.append(row['Comment'])

    num_positive = num_negative = num_neutral = 0
    emotion_counts = {e: 0 for e in EMOTION_KEYWORDS}

    for comment in comments:
        scores = sid.polarity_scores(comment)
        c = scores['compound']
        if c == 0.0:
            num_neutral += 1
        elif c > 0.0:
            num_positive += 1
        else:
            num_negative += 1
        emotion = _detect_emotion(comment)
        emotion_counts[emotion] += 1

    return {
        'num_neutral': num_neutral,
        'num_positive': num_positive,
        'num_negative': num_negative,
        'emotion_counts': emotion_counts,
        'total': len(comments),
    }


# ── Charts ─────────────────────────────────────────────────────────────────────

EMOTION_META = {
    'funny':       {'icon': '😂', 'color': '#FFD93D'},
    'lovely':      {'icon': '❤️',  'color': '#FF6B9D'},
    'angry':       {'icon': '😡', 'color': '#FF4747'},
    'advice':      {'icon': '💡', 'color': '#4FC3F7'},
    'sad':         {'icon': '😢', 'color': '#7E9CC7'},
    'motivational':{'icon': '💪', 'color': '#69DB7C'},
    'spam':        {'icon': '🚫', 'color': '#B0B0B0'},
}


def bar_chart(csv_file: str) -> None:
    results = analyze_sentiment(csv_file)
    df = pd.DataFrame({
        'Sentiment': ['Positive', 'Negative', 'Neutral'],
        'Count': [results['num_positive'], results['num_negative'], results['num_neutral']]
    })
    fig = px.bar(
        df, x='Sentiment', y='Count', color='Sentiment',
        color_discrete_sequence=['#69DB7C', '#FF4747', '#B0B0B0'],
        title='Overall Sentiment Distribution',
        template='plotly_dark'
    )
    fig.update_layout(
        title_font=dict(size=22, family='Georgia'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#e0e0e0',
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_sentiment(csv_file: str) -> None:
    results = analyze_sentiment(csv_file)
    labels = ['Neutral', 'Positive', 'Negative']
    values = [results['num_neutral'], results['num_positive'], results['num_negative']]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values,
        textinfo='label+percent',
        marker=dict(colors=['#B0B0B0', '#69DB7C', '#FF4747'],
                    line=dict(color='#1a1a2e', width=2))
    )])
    fig.update_layout(
        title={'text': 'Sentiment Breakdown', 'font': {'size': 22, 'family': 'Georgia'}, 'x': 0.5},
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#e0e0e0',
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_emotions(csv_file: str) -> None:
    """Radar + bar for the 7-emotion breakdown."""
    results = analyze_sentiment(csv_file)
    ec = results['emotion_counts']

    emotions = list(EMOTION_META.keys())
    counts   = [ec[e] for e in emotions]
    colors   = [EMOTION_META[e]['color'] for e in emotions]
    icons    = [EMOTION_META[e]['icon'] for e in emotions]
    labels   = [f"{icons[i]} {emotions[i].capitalize()}" for i in range(len(emotions))]

    # ── Radar ─────────────────────────────────────────────────────────────────
    fig_radar = go.Figure(data=go.Scatterpolar(
        r=counts + [counts[0]],
        theta=labels + [labels[0]],
        fill='toself',
        fillcolor='rgba(99,102,241,0.25)',
        line=dict(color='#818CF8', width=2),
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, color='#555'),
            angularaxis=dict(color='#aaa'),
        ),
        title={'text': '🎭 Emotion Radar', 'font': {'size': 22, 'family': 'Georgia'}, 'x': 0.5},
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#e0e0e0',
    )

    # ── Horizontal bar ────────────────────────────────────────────────────────
    df = pd.DataFrame({'Emotion': labels, 'Count': counts, 'Color': colors})
    df = df.sort_values('Count', ascending=True)
    fig_bar = go.Figure(go.Bar(
        x=df['Count'], y=df['Emotion'],
        orientation='h',
        marker_color=df['Color'].tolist(),
        text=df['Count'], textposition='outside',
    ))
    fig_bar.update_layout(
        title={'text': '📊 Emotion Frequency', 'font': {'size': 22, 'family': 'Georgia'}, 'x': 0.5},
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#e0e0e0',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        margin=dict(l=150),
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(fig_radar, use_container_width=True)
    with col_b:
        st.plotly_chart(fig_bar, use_container_width=True)
