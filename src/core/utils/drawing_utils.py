import mediapipe as mp

def draw_landmarks(image, pose_results):
    # Рисование ключевых точек тела
    if pose_results is not None and pose_results.pose_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            image,
            pose_results.pose_landmarks,
            mp.solutions.pose.POSE_CONNECTIONS,
            mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp.solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2)
        )