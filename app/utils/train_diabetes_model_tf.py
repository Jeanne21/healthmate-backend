# pyright: reportMissingImports=false
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

def load_and_prepare_data(csv_path):
    df = pd.read_csv(csv_path)

    # Keep only the required columns
    columns_to_keep = ["Age", "Sex", "BMI", "Diabetes"]
    df = df[columns_to_keep]

    # Drop rows with missing values
    df.dropna(inplace=True)

    # Features and label
    X = df.drop(columns=["Diabetes"])
    y = df["Diabetes"]

    return X, y

def train_diabetes_model():
    csv_path = "data\diabetes_data.csv"  

    X, y = load_and_prepare_data(csv_path)

    # Scale the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    # Build the neural network
    model = models.Sequential([
        layers.Input(shape=(X.shape[1],)),
        layers.Dense(16, activation='relu'),
        layers.Dense(8, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    # Train the model
    model.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.1)

    # Evaluate the model
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"✅ Model evaluation on test set:\n   - Loss: {loss:.4f}\n   - Accuracy: {accuracy:.4f}")

    # Save the model and scaler
    os.makedirs("models", exist_ok=True)
    model.save("models/diabetes_model_tf.h5")
    joblib.dump(scaler, "models/diabetes_scaler.pkl")
    print("✅ Diabetes model and scaler saved in 'models/' directory.")

if __name__ == "__main__":
    train_diabetes_model()
