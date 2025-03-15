import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
import os
import csv

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
                    print(f"Successfully loaded {file}")
                    print(f"Columns in {file}: {df.columns.tolist()}")
                    print(f"Sample data from {file}:\n{df.head()}\n")
                    all_data.append(df)
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin1')
                        print(f"Successfully loaded {file} with latin1 encoding")
                        print(f"Columns in {file}: {df.columns.tolist()}")
                        print(f"Sample data from {file}:\n{df.head()}\n")
                        all_data.append(df)
                    except Exception as e:
                        print(f"Error reading file {file} with latin1 encoding: {str(e)}")
                except Exception as e:
                    print(f"Error reading file {file}: {str(e)}")
    
    # Combine all dataframes
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        print("\nCombined Dataset Info:")
        print(f"Total rows: {len(combined_data)}")
        print(f"Columns: {combined_data.columns.tolist()}")
        print("Sample of combined data:")
        print(combined_data.head())
        return combined_data
    else:
        raise ValueError("No valid CSV files found in the specified folder")

def preprocess_data(df):
    """
    Preprocess the text data and prepare for modeling
    """
    # Make a copy to avoid modifying the original dataframe
    df_clean = df.copy()
    
    print("\nInitial Dataset Info:")
    print(f"Total rows: {len(df_clean)}")
    print(f"Columns: {df_clean.columns.tolist()}")
    print(f"Null values:\n{df_clean.isnull().sum()}")
    
    # Remove rows where either text or label is null
    df_clean = df_clean.dropna()
    
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
    print(f"Number of unique labels: {len(y.unique())}")
    print("Label distribution:")
    print(y.value_counts())
    print("\nSample of processed text data:")
    print(X.head())
    print("\nSample of labels:")
    print(y.head())
    
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
    
    print("\nFeature extraction info:")
    print(f"Number of features: {len(vectorizer.get_feature_names_out())}")
    print("Sample features:", vectorizer.get_feature_names_out()[:10])
    
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
    
    print("\nPrediction Details:")
    print(f"Classes: {model.classes_}")
    print(f"Probabilities for each class: {probability[0]}")
    
    return prediction[0], max(probability[0])

def main():
    try:
        # Load data
        print("Loading data...")
        data = load_data()
        
        # Preprocess data
        print("\nPreprocessing data...")
        X, y = preprocess_data(data)
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print("\nTraining model...")
        model, vectorizer = create_and_train_model(X_train, X_test, y_train, y_test)
        
        # Test examples - mix of clear threats and non-threats
        test_texts = [
            "I will find you and kill your entire family, you better watch out!",  # Clear threat
            "You are dead meat, I know where you live and I'm coming for you",     # Clear threat
            "I will hack your system and destroy all your data",                   # Cyber threat
            "Die you piece of trash, I will make you suffer",                      # Violent threat
            "Have a nice day!",                                                    # Non-threat
            "Thank you for your help",                                            # Non-threat
            "I disagree with your opinion",                                       # Non-threat
            "This product is terrible"                                            # Non-threat
        ]
        
        print("\nTesting Examples:")
        print("-" * 50)
        for text in test_texts:
            prediction, confidence = predict_threat(text, model, vectorizer)
            print(f"\nText: {text}")
            print(f"Is Threat: {'Yes' if prediction == 1 else 'No'}")
            print(f"Confidence: {confidence:.2f}")
            print("-" * 50)
        
        return model, vectorizer
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()