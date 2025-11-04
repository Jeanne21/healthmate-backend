# import tensorflow as tf
# import numpy as np

# # Load a TensorFlow model from a given path
# def load_model(path):
#     return tf.keras.models.load_model(path)

# def predict_anomaly(user_profile, measurement, model, measurement_type):
#     """
#     Predicts whether a measurement is anomalous.
    
#     Parameters:
#     - user_profile: dict with 'gender', 'age', 'weight', 'height'
#     - measurement: dict with 'type' and 'value'
#     - model: the preloaded TensorFlow model
#     - measurement_type: one of ["blood_pressure", "blood_sugar"]
#     """

#     gender = 0 if user_profile.get("gender", "male").lower() == "male" else 1
#     age = user_profile.get("age", 30)
#     weight = user_profile.get("weight", 70)
#     height = user_profile.get("height", 170)
#     bmi = round(weight / ((height / 100) ** 2), 2)

#     m_type = measurement.type
#     value = measurement.value

#     if m_type == "blood_pressure" and measurement_type == "blood_pressure":
#         # Use model trained on blood pressure dataset
#         systolic = getattr(value, "systolic", 0)
#         diastolic = getattr(value, "diastolic", 0)
#         pulse = getattr(value, "pulse", 70)

#         X = np.array([[gender, age, systolic, diastolic, bmi, pulse]], dtype=np.float32)

#     elif m_type == "blood_sugar" and measurement_type == "diabetes":
#         # Use model trained on diabetes dataset
#         sugar = float(value)
#         X = np.array([[age, gender, bmi]], dtype=np.float32)

#     else:
#         return False, "Unsupported measurement or mismatched model"

#     # Run model prediction
#     prediction = model.predict(X)[0][0]
#     is_anomaly = prediction > 0.5

#     if is_anomaly:
#         if m_type == "blood_pressure":
#             msg = f"Predicted abnormal blood pressure: {getattr(value, 'systolic', '?')}/{getattr(value, 'diastolic', '?')} mmHg"
#         else:
#             msg = f"Predicted abnormal blood sugar: {value} mg/dL"
#     else:
#         msg = f"{m_type.replace('_', ' ').capitalize()} is normal."

#     return is_anomaly, msg
