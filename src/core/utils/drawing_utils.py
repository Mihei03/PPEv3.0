import cv2
import mediapipe as mp

def draw_landmarks(image, pose_results):
    """Рисование ключевых точек YOLOv11 Pose для нескольких людей"""
    if pose_results is None or not hasattr(pose_results, 'keypoints'):
        return image
    
    # Цвета для разных людей
    colors = [
        (0, 255, 0), (0, 0, 255), (255, 0, 0), 
        (255, 255, 0), (0, 255, 255), (255, 0, 255)
    ]
    
    # Скелетные соединения для YOLOv11 Pose (COCO ключевые точки)
    skeleton = [
        [16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13],
        [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
        [2, 4], [3, 5], [4, 6], [5, 7]
    ]
    
    for i, kpts in enumerate(pose_results.keypoints.xy.cpu().numpy()):
        color = colors[i % len(colors)]
        
        # Рисуем соединения (скелет)
        for u, v in skeleton:
            if kpts[u-1][0] > 0 and kpts[v-1][0] > 0:  # Проверка видимости точек
                start = tuple(map(int, kpts[u-1]))
                end = tuple(map(int, kpts[v-1]))
                cv2.line(image, start, end, color, 2)
        
        # Рисуем ключевые точки
        for kpt in kpts:
            if kpt[0] > 0:  # Проверка видимости точки
                x, y = int(kpt[0]), int(kpt[1])
                cv2.circle(image, (x, y), 5, color, -1)
    
    return image