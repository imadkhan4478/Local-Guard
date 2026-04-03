"""
LocalGuard: Data Preprocessing Pipeline
Cleans and prepares disaster tweet data for ANN training
"""

import pandas as pd
import numpy as np
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

# Download required NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('omw-1.4')

class DisasterTextPreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        
    def clean_text(self, text):
        """Clean and normalize tweet text"""
        if pd.isna(text):
            return ""
        
        text = text.lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'@\w+|#\w+', '', text)
        text = re.sub(r'[^a-z\s]', '', text)
        text = ' '.join(text.split())
        
        words = text.split()
        words = [self.lemmatizer.lemmatize(word) for word in words if word not in self.stop_words]
        
        return ' '.join(words)
    
    def preprocess_dataset(self):
        """Load and preprocess the disaster tweets dataset"""
        print("📊 Loading datasets...")
        
        train_df = pd.read_csv('datasets/train.csv')
        test_df = pd.read_csv('datasets/test.csv')
        
        print(f"✅ Loaded {len(train_df)} training tweets")
        print(f"✅ Loaded {len(test_df)} test tweets")
        print(f"   Disaster tweets in train: {train_df['target'].sum()}")
        print(f"   Safe tweets in train: {len(train_df) - train_df['target'].sum()}")
        
        train_df['text'] = train_df['text'].fillna('')
        test_df['text'] = test_df['text'].fillna('')
        
        print("\n🧹 Cleaning text data...")
        train_df['cleaned_text'] = train_df['text'].apply(self.clean_text)
        test_df['cleaned_text'] = test_df['text'].apply(self.clean_text)
        
        train_df = train_df[train_df['cleaned_text'].str.len() > 0]
        test_df = test_df[test_df['cleaned_text'].str.len() > 0]
        
        print(f"✅ Cleaned {len(train_df)} training tweets")
        print(f"✅ Cleaned {len(test_df)} test tweets")
        
        X_train = train_df['cleaned_text']
        y_train = train_df['target']
        X_test = test_df['cleaned_text']
        
        if 'target' in test_df.columns:
            y_test = test_df['target']
        else:
            print("\n⚠️  Test set has no labels. Splitting training data...")
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
            )
        
        print(f"\n📈 Final split:")
        print(f"   Training set: {len(X_train)} samples")
        print(f"   Test set: {len(X_test)} samples")
        
        print("\n🔢 Converting text to TF-IDF vectors...")
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        print(f"✅ Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        
        X_train_dense = X_train_vec.toarray()
        X_test_dense = X_test_vec.toarray()
        
        os.makedirs('models', exist_ok=True)
        with open('models/vectorizer.pkl', 'wb') as f:
            pickle.dump(self.vectorizer, f)
        print("💾 Saved vectorizer to models/vectorizer.pkl")
        
        self.save_samples(X_train, X_test, y_train, y_test)
        
        return X_train_dense, X_test_dense, y_train.values, y_test.values
    
    def save_samples(self, X_train, X_test, y_train, y_test):
        """Save sample texts for app display"""
        samples = {
            'train_texts': X_train.head(100).tolist(),
            'train_labels': y_train.head(100).tolist(),
            'test_texts': X_test.head(100).tolist(),
            'test_labels': y_test.head(100).tolist()
        }
        with open('models/sample_texts.pkl', 'wb') as f:
            pickle.dump(samples, f)

def main():
    """Run preprocessing pipeline"""
    preprocessor = DisasterTextPreprocessor()
    X_train, X_test, y_train, y_test = preprocessor.preprocess_dataset()
    
    print("\n💾 Saving processed data...")
    np.save('models/X_train.npy', X_train)
    np.save('models/X_test.npy', X_test)
    np.save('models/y_train.npy', y_train)
    np.save('models/y_test.npy', y_test)
    
    print("\n✅ Preprocessing complete!")
    print(f"   Training features shape: {X_train.shape}")
    print(f"   Test features shape: {X_test.shape}")
    print("\n🎯 Next step: Run 'python train.py' to train the model")

if __name__ == "__main__":
    main()