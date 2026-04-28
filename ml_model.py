from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np

# -------------------- TRAINING DATA --------------------

training_data = {
    "Dental Problem": [
        "tooth pain",
        "gum swelling",
        "tooth ache bleeding",
        "jaw pain dental infection"
    ],
    "Viral Infection": [
        "fever cough cold",
        "body pain fever",
        "sore throat cold flu",
        "runny nose cough"
    ],
    "Heart/Lung Emergency": [
        "chest pain breath issue",
        "shortness of breath chest tightness",
        "heart pain difficulty breathing",
        "breathing problem severe chest pain"
    ],
    "Migraine / Neurological": [
        "headache vomiting",
        "severe headache light sensitivity",
        "migraine nausea dizziness",
        "head pain vision blur"
    ]
}

# -------------------- PREPARE DATA --------------------

texts = []
labels = []

for disease, symptoms in training_data.items():
    for s in symptoms:
        texts.append(s)
        labels.append(disease)

# -------------------- VECTORIZE --------------------

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# -------------------- TRAIN MODEL --------------------

model = MultinomialNB()
model.fit(X, labels)

# -------------------- PREDICTION FUNCTION --------------------

def predict_disease(user_input):
    user_input = user_input.lower()

    X_test = vectorizer.transform([user_input])

    prediction = model.predict(X_test)[0]

    probabilities = model.predict_proba(X_test)[0]
    confidence = np.max(probabilities) * 100

    return {
        "disease": prediction,
        "confidence": round(confidence, 2)
    }