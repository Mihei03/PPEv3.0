import cv2
import mediapipe as mp

def draw_landmarks(image, pose_results, face_results):
    # Рисование ключевых точек тела
    if pose_results.pose_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            image,
            pose_results.pose_landmarks,
            mp.solutions.pose.POSE_CONNECTIONS,
            mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp.solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )

    # Рисование ключевых точек лица
    if face_results.multi_face_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                image,
                face_landmarks,
                mp.solutions.face_mesh.FACEMESH_CONTOURS,
                mp.solutions.drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=1, circle_radius=1),
                mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=1)
            )

def draw_siz_status(image, siz_detected):
    """Отрисовка статуса СИЗ (всегда отображается)"""
    if siz_detected:
        cv2.putText(image, "SIZ Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        cv2.putText(image, "SIZ Not Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)