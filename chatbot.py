import re
import pandas as pd
import numpy as np
import difflib

def process_query(query, df):
    """
    Process natural language queries into pandas data operations using enhanced NLP.
    Returns a dictionary: {"text": "...", "chart_data": {...}}
    """
    response = {"text": "", "chart_data": None}
    
    if df is None or df.empty:
        response["text"] = "No data available. Please upload and clean a dataset first."
        return response
        
    query_lower = query.lower()
    
    # 0. Greetings
    greetings = ["hello", "hi", "hey", "how are you", "good morning", "good evening"]
    if any(query_lower.startswith(g) or query_lower == g for g in greetings):
        response["text"] = "Hello there! 👋 I am your AI Health Assistant. You can ask me to visualize data, count patients with specific conditions, or calculate averages. How can I help you today?"
        return response
    
    # Define a synonym dictionary for healthcare terminology
    synonyms = {
        "bp": ["blood_pressure", "bp", "bloodpressure", "pressure", "hypertension"],
        "sugar": ["glucose", "sugar", "diabetes", "hba1c"],
        "heart rate": ["pulse", "heart_rate", "hr", "heartrate"],
        "age": ["age", "years", "dob", "old", "young"],
        "gender": ["sex", "gender", "male", "female"],
        "disease": ["diagnosis", "condition", "illness", "disease", "sickness", "problem"],
        "severity": ["level", "stage", "severity"],
        "cholesterol": ["chol", "cholesterol", "lipid"]
    }

    def find_col(keywords):
        columns_lower = [c.lower() for c in df.columns]
        for k in keywords:
            if len(k) < 2: continue
            for c in df.columns:
                if k in c.lower() or c.lower() in k:
                    return c
            for key, syn_list in synonyms.items():
                if k in key or k in syn_list:
                    for c in df.columns:
                        for syn in syn_list:
                            if syn in c.lower():
                                return c
            matches = difflib.get_close_matches(k, columns_lower, n=1, cutoff=0.7)
            if matches:
                for c in df.columns:
                    if c.lower() == matches[0]:
                        return c
        return None

    def generate_chart(col_name):
        if pd.api.types.is_numeric_dtype(df[col_name]):
            return {
                "type": "histogram",
                "x": df[col_name].dropna().tolist(),
                "title": f"Distribution of {col_name.capitalize()}",
                "xaxis": col_name.capitalize(),
                "marker": {"color": "#00b4d8"}
            }
        else:
            counts = df[col_name].value_counts().head(10)
            return {
                "type": "bar",
                "x": counts.index.astype(str).tolist(),
                "y": counts.values.tolist(),
                "title": f"Distribution of {col_name.capitalize()}",
                "xaxis": col_name.capitalize(),
                "yaxis": "Count",
                "marker": {"color": "#0077b6"}
            }

    # 1. Personal / Chart Request (e.g. "how much is my sugar level", "visualize bp")
    viz_keywords = ["my", "visualize", "chart", "graph", "plot", "show me"]
    if any(kw in query_lower for kw in viz_keywords):
        # Find which column they are talking about
        words = query_lower.split()
        target_col = find_col(words)
        
        if target_col:
            response["text"] = f"Since I am analyzing a hospital-wide dataset of {len(df)} patients, I cannot access your personal data. However, here is the visualized distribution of '{target_col}' across all patients in the dataset!"
            response["chart_data"] = generate_chart(target_col)
            return response

    # 2. Ill / Sick semantic understanding
    ill_keywords = ["ill", "sick", "unhealthy"]
    if any(kw in query_lower for kw in ill_keywords):
        disease_col = find_col(["disease"])
        if disease_col:
            # Assume ill means they have some disease that is not "none", "healthy", "n/a", etc.
            healthy_terms = ["none", "healthy", "n/a", "no", "normal"]
            df_ill = df[~df[disease_col].astype(str).str.lower().isin(healthy_terms)]
            # Also drop na
            df_ill = df_ill.dropna(subset=[disease_col])
            response["text"] = f"Based on the '{disease_col}' records, there are {len(df_ill)} patients who are currently classified as ill (having a recorded diagnosis)."
            return response

    # 3. Count query (e.g., "count patients with diabetes", "who has high bp")
    count_keywords = ["count", "how many", "number of", "who has", "who have"]
    if any(kw in query_lower for kw in count_keywords):
        split_words = ["with", "has", "having", "diagnosed"]
        condition = None
        for w in split_words:
            if f" {w} " in query_lower:
                condition = query_lower.split(f" {w} ")[-1].strip()
                break
        
        if condition:
            for col in df.columns:
                if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
                    unique_vals = [str(v) for v in df[col].dropna().unique()]
                    for val in unique_vals:
                        if condition in val.lower() or val.lower() in condition:
                            count = df[df[col].astype(str).str.lower().str.contains(val.lower(), na=False)].shape[0]
                            response["text"] = f"Found {count} patients matching '{val}' in the '{col}' column."
                            return response
                            
                    matches = difflib.get_close_matches(condition, [v.lower() for v in unique_vals], n=1, cutoff=0.6)
                    if matches:
                        match_val = matches[0]
                        for original_val in unique_vals:
                            if original_val.lower() == match_val:
                                count = df[df[col].astype(str) == original_val].shape[0]
                                response["text"] = f"Found {count} patients with '{original_val}' in the '{col}' column."
                                return response
            
            response["text"] = f"Could not find any specific records matching '{condition}'. Try being more specific."
            return response
        else:
            response["text"] = f"There are {len(df)} total patient records in this dataset."
            return response

    # 4. Average query
    avg_keywords = ["average", "avg", "mean", "median"]
    if any(kw in query_lower for kw in avg_keywords):
        clean_q = query_lower
        for kw in avg_keywords:
            clean_q = clean_q.replace(kw, "")
        words = clean_q.strip().split()
        target_col = find_col(words)
        
        if target_col:
            if pd.api.types.is_numeric_dtype(df[target_col]):
                avg_val = df[target_col].mean()
                response["text"] = f"The average {target_col} is {avg_val:.2f}."
                return response
            else:
                response["text"] = f"I found the column '{target_col}', but it doesn't contain numerical data to average."
                return response
        response["text"] = "I couldn't figure out which numerical column you want the average for."
        return response

    # 5. Filter query
    filter_match = re.search(r'(above|over|greater than|more than|>|below|under|less than|<)\s+(\d+)', query_lower)
    if filter_match:
        operator_str = filter_match.group(1)
        value = int(filter_match.group(2))
        words = query_lower.replace(operator_str, "").replace(str(value), "").split()
        target_col = find_col(words)
        
        if not target_col:
            target_col = find_col(["age"])
            
        if target_col and pd.api.types.is_numeric_dtype(df[target_col]):
            if operator_str in ["above", "over", "greater than", "more than", ">"]:
                filtered = df[df[target_col] > value]
                response["text"] = f"Found {len(filtered)} patients with {target_col} > {value}."
            else:
                filtered = df[df[target_col] < value]
                response["text"] = f"Found {len(filtered)} patients with {target_col} < {value}."
            return response
    
    # 6. Summary / General
    if "summary" in query_lower or "describe" in query_lower or "overview" in query_lower:
        num_patients = len(df)
        num_cols = len(df.columns)
        response["text"] = f"The dataset contains {num_patients} patient records and {num_cols} data points (columns). Columns include: {', '.join(df.columns[:5])}..."
        return response

    response["text"] = "Hmm, I didn't quite catch that. You can ask me to visualize something (like 'visualize my sugar levels'), count patients with a condition, or get an average."
    return response
