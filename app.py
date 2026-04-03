"""
LocalGuard: Interactive Disaster Detection Web App
Streamlit interface for real-time disaster tweet classification with API verification
"""

import streamlit as st
import torch
import torch.nn as nn
import numpy as np
import pickle
import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="LocalGuard - Disaster Detection", page_icon="🚨", layout="wide")

st.markdown("""
    <style>
    .main-header {font-size: 3rem; color: #FF4B4B; text-align: center; margin-bottom: 0;}
    .sub-header {text-align: center; color: #666; margin-bottom: 2rem;}
    .disaster-alert {background-color: #FFE5E5; border-left: 5px solid #FF4B4B; padding: 1rem; margin: 1rem 0;}
    .safe-alert {background-color: #E5F5E5; border-left: 5px solid #4BB543; padding: 1rem; margin: 1rem 0;}
    </style>
""", unsafe_allow_html=True)

class DisasterANN(nn.Module):
    def __init__(self, input_size):
        super(DisasterANN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 1), nn.Sigmoid()
        )
    def forward(self, x):
        return self.network(x)

@st.cache_resource
def load_models():
    try:
        with open('models/vectorizer.pkl', 'rb') as f:
            vectorizer = pickle.load(f)
        input_size = len(vectorizer.vocabulary_)
        model = DisasterANN(input_size)
        model.load_state_dict(torch.load('models/final_model.pth', map_location='cpu'))
        model.eval()
        return model, vectorizer
    except FileNotFoundError:
        st.error("⚠️ Models not found! Please run preprocess.py and train.py first.")
        st.stop()

def clean_text(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = re.sub(r'@\w+|#\w+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = ' '.join(text.split())
    words = [lemmatizer.lemmatize(w) for w in text.split() if w not in stop_words]
    return ' '.join(words)

def predict_disaster(text, model, vectorizer):
    cleaned = clean_text(text)
    if not cleaned:
        return None, 0.5
    vector = vectorizer.transform([cleaned]).toarray()
    tensor = torch.FloatTensor(vector)
    with torch.no_grad():
        output = model(tensor)
        probability = output.item()
    return probability > 0.5, probability

# Import credibility checker
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Import credibility checker
try:
    from credibility_checker import CredibilityChecker
    from config import (OPENWEATHER_API_KEY, NEWS_API_KEY, NASA_FIRMS_API_KEY,
                       TWITTER_API_KEY, TWITTER_API_SECRET, AQI_API_KEY, 
                    )
    credibility_checker = CredibilityChecker(
        weather_api_key=OPENWEATHER_API_KEY,
        news_api_key=NEWS_API_KEY,
        nasa_key=NASA_FIRMS_API_KEY,
        twitter_key=TWITTER_API_KEY,
        twitter_secret=TWITTER_API_SECRET,
        aqi_key=AQI_API_KEY,
        
    )
    CREDIBILITY_ENABLED = True
    API_ENABLED = (OPENWEATHER_API_KEY != "YOUR_OPENWEATHER_API_KEY_HERE")
except ImportError as e:
    CREDIBILITY_ENABLED = False
    API_ENABLED = False
    print(f"Credibility checker not loaded: {e}")

def main():
    st.markdown('<h1 class="main-header">🚨 LocalGuard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Hyper-Local Disaster Detection with Real-Time Verification</p>', unsafe_allow_html=True)
    
    model, vectorizer = load_models()
    
    with st.sidebar:
        st.header("📊 About")
        st.write("LocalGuard uses AI + Real-time Data to detect disasters and verify information.")
        
        st.header("🎯 Features")
        st.write("✅ Disaster language detection")
        st.write("✅ Credibility scoring")
        st.write("✅ Weather verification")
        st.write("✅ News cross-reference")
        
        if API_ENABLED:
            st.success("🌐 Weather API: ENABLED")
        else:
            st.warning("🌐 Weather API: DISABLED")
            st.info("API will activate in 10-15 minutes after signup")
        
        st.header("📈 Model Info")
        try:
            X_test = np.load('models/X_test.npy')
            y_test = np.load('models/y_test.npy')
            with torch.no_grad():
                outputs = model(torch.FloatTensor(X_test))
                predictions = (outputs > 0.5).float().numpy()
                accuracy = (predictions.flatten() == y_test).mean()
            st.metric("Test Accuracy", f"{accuracy:.2%}")
            st.metric("Vocabulary Size", f"{len(vectorizer.vocabulary_):,}")
        except:
            st.write("Run training first")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Single Prediction", "📁 Batch Prediction", "📊 Sample Data", "📈 Performance"])
    
    with tab1:
        st.header("Analyze a Single Text")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            user_input = st.text_area("Enter text:", height=150, 
                                     placeholder="e.g., 'Heavy rainfall in Lahore causing floods on Mall Road'")
        
        with col2:
            st.write("**Quick Examples:**")
            examples = {
                "🌧️ Rain/Flood": "Heavy rainfall in Lahore causing floods on Mall Road",
                "🔥 Fire": "Fire at Centaurus Mall Islamabad, evacuations underway",
                "✅ Metaphor": "I'm drowning in homework this week",
                "❌ Fake": "BREAKING!!! SHARE NOW!!! Earthquake in Karachi!!!"
            }
            
            for label, text in examples.items():
                if st.button(label, key=label, use_container_width=True):
                    user_input = text
        
        if st.button("🔍 Analyze Text", type="primary", use_container_width=True):
            if user_input:
                with st.spinner("Analyzing text and verifying with real-time data..."):
                    is_disaster, confidence = predict_disaster(user_input, model, vectorizer)
                    if is_disaster is None:
                        st.warning("⚠️ Text too short")
                    else:
                        # Generate credibility report
                        if CREDIBILITY_ENABLED:
                            cred_report = credibility_checker.generate_comprehensive_report(
                                user_input, is_disaster, confidence
                            )
                        
                        if is_disaster:
                            st.markdown(f"""<div class="disaster-alert"><h2>🚨 DISASTER DETECTED</h2>
                            <p><strong>AI Confidence:</strong> {confidence:.1%}</p></div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div class="safe-alert"><h2>✅ SAFE / NON-DISASTER</h2>
                            <p><strong>Confidence:</strong> {(1-confidence):.1%}</p></div>""", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Disaster Probability", f"{confidence:.1%}")
                        col2.metric("Safe Probability", f"{(1-confidence):.1%}")
                        st.progress(confidence)
                        
                        # Show credibility analysis
                        if CREDIBILITY_ENABLED and is_disaster:
                            st.markdown("---")
                            st.subheader("🔍 Comprehensive Verification Report")
                            
                            # Main metrics
                            col1, col2, col3 = st.columns(3)
                            col1.metric(
                                "Linguistic Score", 
                                f"{cred_report['linguistic_score']}%",
                                help="Based on language analysis"
                            )
                            col2.metric(
                                "Final Credibility", 
                                f"{cred_report['final_credibility_score']}%",
                                help="Combined score with API verification"
                            )
                            col3.metric("Risk Level", cred_report['risk_level'])
                            
                            # Overall status
                            if "VERIFIED" in cred_report['overall_status']:
                                st.success(f"**{cred_report['overall_status']}**")
                            elif "PARTIALLY" in cred_report['overall_status']:
                                st.warning(f"**{cred_report['overall_status']}**")
                            else:
                                st.error(f"**{cred_report['overall_status']}**")
                            
                            st.info(f"💡 **Recommendation:** {cred_report.get('recommendation', 'No recommendation available')}")

                            
                            # Location detection
                            if cred_report['location_detected']:
                                st.write(f"📍 **Location Detected:** {cred_report['location_detected']}")
                            
                            # Verification details
                            if cred_report['verification_details']:
                                st.markdown("### 🌐 Real-Time Verification")
                                for verification in cred_report['verification_details']:
                                    with st.expander(f"{verification['type']} - {verification['status']}", expanded=True):
                                        for detail in verification['details']:
                                            st.write(detail)
                                        
                                        # Show weather data
                                        if verification['type'] == 'Weather Verification' and cred_report.get('weather_data'):

                                            weather = cred_report['weather_data']['weather_data']
                                            col1, col2, col3 = st.columns(3)
                                            col1.metric("Conditions", weather['description'].title())
                                            col2.metric("Temperature", f"{weather['temp']:.1f}°C")
                                            col3.metric("Humidity", f"{weather['humidity']}%")
                                            if weather['rain'] > 0:
                                                st.success(f"🌧️ Rain detected: {weather['rain']} mm/hr")
                                        
                                        # Show news articles
                                        if verification['type'] == 'News Verification' and cred_report['news_data']:
                                            if cred_report['news_data']['articles']:
                                                st.write("**Related News Articles:**")
                                                for article in cred_report['news_data']['articles'][:3]:
                                                    st.write(f"• [{article['source']}] {article['title']}")
                                                    st.caption(f"🔗 [Read more]({article['url']})")
                            
                            # Show warnings
                            if cred_report['warnings']:
                                with st.expander("⚠️ Warning Signs", expanded=False):
                                    for warning in cred_report['warnings']:
                                        st.write(warning)
                            
                            # Show positive signals
                            if cred_report['positive_signals']:
                                with st.expander("✅ Positive Indicators"):
                                    for signal in cred_report['positive_signals']:
                                        st.write(signal)
                            
                            # Show detailed flags
                            if cred_report.get('flags'):

                                with st.expander("🔎 Detailed Analysis"):
                                    for flag in cred_report['flags']:
                                        st.write(f"• {flag}")
            else:
                st.warning("⚠️ Please enter text")
    
    with tab2:
        st.header("Batch Analysis")
        uploaded_file = st.file_uploader("Upload CSV with 'text' column", type="csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            if 'text' not in df.columns:
                st.error("❌ Need 'text' column")
            else:
                st.write(f"Loaded {len(df)} texts")
                if st.button("🚀 Analyze All"):
                    results = []
                    progress_bar = st.progress(0)
                    for idx, text in enumerate(df['text']):
                        is_disaster, confidence = predict_disaster(str(text), model, vectorizer)
                        results.append({'text': text, 'prediction': 'Disaster' if is_disaster else 'Safe', 'confidence': f"{confidence:.1%}"})
                        progress_bar.progress((idx + 1) / len(df))
                    results_df = pd.DataFrame(results)
                    st.success("✅ Complete!")
                    st.dataframe(results_df, use_container_width=True)
                    st.download_button("📥 Download", results_df.to_csv(index=False), "predictions.csv", "text/csv")
    
    with tab3:
        st.header("Sample Predictions")
        try:
            with open('models/sample_texts.pkl', 'rb') as f:
                samples = pickle.load(f)
            show_type = st.radio("Show:", ["Disaster Examples", "Safe Examples"])
            if show_type == "Disaster Examples":
                texts = [samples['test_texts'][i] for i in range(len(samples['test_texts'])) if samples['test_labels'][i] == 1][:10]
            else:
                texts = [samples['test_texts'][i] for i in range(len(samples['test_texts'])) if samples['test_labels'][i] == 0][:10]
            for text in texts:
                with st.expander(f"{text[:80]}..."):
                    st.write(f"**Full:** {text}")
                    _, conf = predict_disaster(text, model, vectorizer)
                    st.metric("Confidence", f"{conf:.1%}")
        except:
            st.warning("⚠️ Run training first")
    
    with tab4:
        st.header("Model Performance")
        try:
            st.subheader("Training History")
            st.image('models/training_history.png', use_container_width=True)
            
            st.subheader("Test Performance")
            X_test = np.load('models/X_test.npy')
            y_test = np.load('models/y_test.npy')
            with torch.no_grad():
                outputs = model(torch.FloatTensor(X_test))
                predictions = (outputs > 0.5).float().numpy().flatten()
            
            from sklearn.metrics import classification_report, confusion_matrix
            accuracy = (predictions == y_test).mean()
            st.metric("Accuracy", f"{accuracy:.2%}")
            
            cm = confusion_matrix(y_test, predictions)
            fig, ax = plt.subplots(figsize=(6, 5))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                       xticklabels=['Safe', 'Disaster'], yticklabels=['Safe', 'Disaster'])
            ax.set_ylabel('Actual')
            ax.set_xlabel('Predicted')
            ax.set_title('Confusion Matrix')
            st.pyplot(fig)
            
            st.text(classification_report(y_test, predictions, target_names=['Safe', 'Disaster']))
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()