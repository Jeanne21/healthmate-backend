# # pyright: reportMissingImports=false
# import numpy as np
# import pandas as pd
# import tensorflow as tf
# from tensorflow.keras import layers, models
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import StandardScaler
# import joblib
# import os

# # 1. Load and clean real dataset
# def load_and_prepare_data(csv_path):
#     df = pd.read_csv(csv_path)

#     # Keep only relevant columns
#     columns_to_keep = ["male", "age", "sysBP", "diaBP", "BMI", "heartRate", "Risk"]
#     df = df[columns_to_keep]

#     # Drop rows with missing values in those columns (if any)
#     df.dropna(inplace=True)

#     X = df.drop(columns=["Risk"])
#     y = df["Risk"]

#     return X, y

# # 2. Train and save model
# def train_tf_model():
#     csv_path = "data\Hypertension-risk-model-main.csv"  

#     X, y = load_and_prepare_data(csv_path)

#     # Scale input features
#     scaler = StandardScaler()
#     X_scaled = scaler.fit_transform(X)

#     # Split data
#     X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

#     # Build model
#     model = models.Sequential([
#         layers.Input(shape=(X.shape[1],)),
#         layers.Dense(32, activation='relu'),
#         layers.Dense(16, activation='relu'),
#         layers.Dense(1, activation='sigmoid')  # Binary classification
#     ])

#     model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

#     # Train
#     model.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.1)

#     # Evaluate the model
#     loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
#     print(f"✅ Model evaluation on test set:\n   - Loss: {loss:.4f}\n   - Accuracy: {accuracy:.4f}")

#     # Save model and scaler
#     os.makedirs("models", exist_ok=True)
#     model.save("models/bp_model_tf.h5")
#     joblib.dump(scaler, "models/bp_scaler.pkl")
#     print("✅ TensorFlow model and scaler saved in 'models/' directory.")

# if __name__ == "__main__":
#     train_tf_model()
