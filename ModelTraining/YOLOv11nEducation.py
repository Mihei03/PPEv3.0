from ultralytics import YOLO

# Загрузка модели
model = YOLO("yolo11n.pt")  # предварительно обученная модель

# Обучение модели
results = model.train(
    data = 'C:/Users/Mihei/Desktop/PPEv2/data.yaml',  # ваш конфиг с путями к данным
    epochs=350,  # увеличил количество эпох
    imgsz=640,
    batch=8,  # уменьшил batch для избежания OOM ошибок
    device="mps",  # или "cuda" для NVIDIA GPU, "cpu" для CPU
    patience=15,  # больше терпения для ранней остановки
    lr0=0.01,
    lrf=0.1,
    weight_decay=0.0005,
    optimizer="AdamW",  # явно указал оптимизатор
    seed=42,
    overlap_mask=True,
    plots=True,  # включить графики
    save=True,
    save_period=10,  # сохранять чекпоинты каждые 10 эпох
    val=True,
)