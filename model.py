import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix

def train_model(df):
    """
    Dynamically select target, split data, train model, and return metrics.
    """
    if df is None or df.empty or len(df.columns) < 2:
        return 0.0, [], []

    # Dynamic target detection
    target_candidates = ["outcome", "target", "readmission", "diagnosis", "disease", "status", "label"]
    target_col = None
    
    # Check if any common target column exists
    for col in df.columns:
        if col.lower() in target_candidates:
            target_col = col
            break
            
    # Fallback to the last column if no known target column is found
    if not target_col:
        target_col = df.columns[-1]

    # Features and Target
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Train Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Random Forest (Optimized for speed and low server load)
    # 50 trees are usually sufficient for healthcare data analysis in this context
    model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)
    
    # Metrics
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    # Feature Importances
    importances = model.feature_importances_
    features = X.columns.tolist()
    feature_importance = [{"feature": f, "importance": float(i)} for f, i in zip(features, importances)]
    feature_importance = sorted(feature_importance, key=lambda x: x["importance"], reverse=True)

    return round(acc * 100, 2), cm, feature_importance[:10]  # top 10 features
