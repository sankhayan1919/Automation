import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import os
import csv  # Adding csv import

def load_data(folder_path='Vulgar_dataset'):
    """
    Load and combine data from all csv files in the specified folder
    """
    all_data = []
    
    # Walk through all files in the folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.csv'):
                file_path = os.path.join(root, file)
                try:
                    # Read csv file with explicit encoding
                    df = pd.read_csv(file_path, encoding='utf-8')
                    all_data.append(df)
                except UnicodeDecodeError:
                    # Try different encoding if utf-8 fails
                    try:
                        df = pd.read_csv(file_path, encoding='latin1')
                        all_data.append(df)
                    except Exception as e:
                        print(f"Error reading file {file} with latin1 encoding: {str(e)}")
                except Exception as e:
                    print(f"Error reading file {file}: {str(e)}")
    
    # Combine all dataframes
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        return combined_data
    else:
        raise ValueError("No valid CSV files found in the specified folder")

def preprocess_data(df):
    """
    Preprocess the text data and prepare for modeling
    """
    # Make a copy to avoid modifying the original dataframe
    df_clean = df.copy()
    
    # Print initial information about the dataset
    print("\nInitial Dataset Info:")
    print(f"Total rows: {len(df_clean)}")
    print(f"Null values:\n{df_clean.isnull().sum()}")
    
    # Remove rows where either text or label is null
    df_clean = df_clean.dropna()
    
    print("\nAfter removing null values:")
    print(f"Remaining rows: {len(df_clean)}")
    
    # Convert text column to string and clean it
    X = df_clean.iloc[:, 0].astype(str)
    X = X.apply(lambda x: x.strip())  # Remove leading/trailing whitespace
    X = X.replace('', np.nan)  # Convert empty strings to NaN
    X = X.dropna()  # Remove any remaining empty strings
    
    # Get corresponding labels
    y = df_clean.iloc[:, 1]
    
    # Ensure X and y have the same length
    common_index = X.index.intersection(y.index)
    X = X.loc[common_index]
    y = y.loc[common_index]
    
    print("\nFinal cleaned dataset:")
    print(f"Number of samples: {len(X)}")
    print(f"Number of labels: {len(y)}")
    print(f"Number of unique labels: {len(y.unique())}")
    print("Label distribution:")
    print(y.value_counts())
    
    return X, y

def create_and_train_model(X_train, X_test, y_train, y_test):
    """
    Create, train and evaluate the model
    """
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    
    # Transform the text data
    X_train_vectorized = vectorizer.fit_transform(X_train)
    X_test_vectorized = vectorizer.transform(X_test)
    
    # Create and train the model
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_train_vectorized, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test_vectorized)
    
    # Print model performance
    print("\nModel Performance:")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return model, vectorizer

def predict_threat(text, model, vectorizer):
    """
    Make predictions on new text
    """
    # Transform the new text
    text_vectorized = vectorizer.transform([text])
    
    # Make prediction
    prediction = model.predict(text_vectorized)
    probability = model.predict_proba(text_vectorized)
    
    return prediction[0], max(probability[0])

def main():
    try:
        # Load data
        print("Loading data...")
        data = load_data()
        
        # Preprocess data
        print("Preprocessing data...")
        X, y = preprocess_data(data)
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train and evaluate model
        print("Training model...")
        model, vectorizer = create_and_train_model(X_train, X_test, y_train, y_test)
        
        # Example prediction
        print("\nExample Prediction:")
        sample_text = "I want to see the whole kashmir burning and people crying. Pakistani bomber planes will do carpet bombing around the Dal Lake."
        prediction, confidence = predict_threat(sample_text, model, vectorizer)
        print(f"Text: {sample_text}")
        print(f"Prediction: {prediction}")
        print(f"Confidence: {confidence:.2f}")
        
        return model, vectorizer
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 