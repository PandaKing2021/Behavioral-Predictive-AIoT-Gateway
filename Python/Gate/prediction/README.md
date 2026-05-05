# AI Behavior Prediction & Scene Linkage System

An edge-deployed user behavior prediction and adaptive scene linkage system based on a CNN-LSTM hybrid model, deployed at the gateway layer with a lightweight neural network to achieve "unnoticeable" automated scene control in smart homes.

## 🌟 Core Features

- **Lightweight Model**: Edge1DCLSTM model with only ~12.7K parameters, inference latency < 5ms
- **Edge-Cloud Collaboration**: Sentinel model for fast initial screening, full model awakened for low-confidence cases
- **Adaptive Learning**: Learns user behavior patterns from historical sensor data
- **Intelligent Degradation**: Automatically falls back to threshold-based decisions when model is abnormal
- **Scene Linkage**: Prediction-driven intelligent scene triggering with customizable configuration

## 📋 System Architecture

```
Sensor Data → Data Collection → Preprocessing → CNN-LSTM Inference → Scene Linkage → Device Control
                ↓                    ↓
            MySQL History DB      ONNX Engine
                                      ↓
                              Sentinel (Edge-Cloud Collaboration)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd Python
pip install -r requirements.txt
```

### 2. Train Model (Optional)

If you need to train your own model:

```bash
cd scripts
python train_model.py --epochs 50 --batch_size 32
```

### 3. Export ONNX Model

```bash
python export_onnx.py
```

This will generate two ONNX model files:
- `Gate/models/edge_1dcnn_lstm.onnx` - Edge model
- `Gate/models/sentinel_lstm.onnx` - Sentinel model

### 4. Run Integration Test

```bash
python test_prediction_integration.py
```

### 5. Start Gateway

```bash
cd Gate
python gate.py
```

## 📁 Directory Structure

```
Python/
├── Gate/
│   ├── prediction/                    # Prediction module
│   │   ├── __init__.py               # Module initialization
│   │   ├── config.py                 # Configuration file
│   │   ├── data_collector.py         # Data collector
│   │   ├── data_preprocessor.py      # Data preprocessor
│   │   ├── onnx_inference.py         # ONNX inference engine
│   │   └── precontroller.py          # Precontroller
│   ├── models/                        # ONNX model files
│   │   ├── edge_1dcnn_lstm.onnx      # Edge model
│   │   └── sentinel_lstm.onnx        # Sentinel model
│   ├── sensor_handler.py             # Sensor handler (integrated with prediction)
│   └── gate.py                       # Gateway main program
├── scripts/
│   ├── train_model.py                # Model training script
│   ├── export_onnx.py                # ONNX export script
│   ├── evaluate_model.py             # Model evaluation script
│   └── test_prediction_integration.py # Integration test script
└── requirements.txt                  # Dependencies list
```

## ⚙️ Configuration

### Model Configuration (prediction/config.py)

```python
# Sequence length
SEQUENCE_LENGTH = 10

# Feature dimension
FEATURE_DIM = 6  # Temperature, humidity, brightness, AC state, light state, curtain state

# Sentinel confidence threshold
SENTINEL_THRESHOLD = 0.9

# Scene trigger threshold
SCENE_TRIGGER_THRESHOLD = 0.7
```

### Scene Configuration

Default scene templates:

1. **Auto Turn On AC**: Prediction > 0.7 and temperature > 28°C
2. **Auto Turn Off AC**: Prediction < 0.3 and temperature < 25°C
3. **Auto Lights On Curtains Closed**: Prediction > 0.6 and brightness < 100
4. **Auto Lights Off Curtains Open**: Prediction < 0.4 and brightness > 200

Scenes can be customized by modifying the `_load_default_scenes()` method in `precontroller.py`.

## 📊 Performance Metrics

- **Model Size**: Edge model ~50KB, Sentinel model ~10KB
- **Inference Latency**: Edge model ~2.5ms, Sentinel model ~1ms
- **Memory Usage**: <10MB
- **Accuracy**: 92.34% (CASAS dataset)

## 🔧 Advanced Features

### Custom Scenes

Create a JSON configuration file:

```json
{
  "scenes": [
    {
      "scene_id": "custom_scene_1",
      "name": "Custom Scene",
      "description": "Scene description",
      "trigger_conditions": {
        "prediction_min": 0.7,
        "Temperature_max": 28.0
      },
      "actions": {
        "Light_TH": 1,
        "Light_CU": 0
      },
      "priority": 10,
      "cooldown": 300
    }
  ]
}
```

Then specify the configuration file path when initializing the Precontroller:

```python
controller = Precontroller(scene_config_path="path/to/scenes.json")
```

### Performance Monitoring

View inference statistics:

```python
stats = prediction_engine.get_stats()
print(f"Total inferences: {stats['total_inferences']}")
print(f"Wake rate: {stats['wake_rate']:.2%}")
print(f"Average latency: {stats['avg_latency_ms']:.2f}ms")
```

## 🐛 Troubleshooting

### Model File Not Found

**Error**: `Edge model file not found: .../edge_1dcnn_lstm.onnx`

**Solution**:
```bash
cd scripts
python train_model.py
python export_onnx.py
```

### Normalization Parameters Not Fitted

**Error**: `Normalization parameters not fitted`

**Solution**: Ensure sufficient historical data (at least 100 records). The system will automatically fit normalization parameters on first run.

### Inference Failed

**Error**: `AI prediction decision failed`

**Solution**: The system will automatically degrade to threshold-based decision mode. Check the logs for detailed error information.

## 📚 API Documentation

### DataCollector

```python
collector = DataCollector(db_conn, cache_hours=168)
collector.update_cache(incremental=True)
features = collector.get_latest_samples(n_samples=10)
```

### DataPreprocessor

```python
preprocessor = DataPreprocessor(feature_columns, normalization_method="minmax")
features = preprocessor.fit_transform(df)
sequences = preprocessor.create_sequences(features, seq_length=10)
```

### ONNXModelInference

```python
engine = ONNXModelInference(edge_model_path, sentinel_model_path, threshold=0.9)
engine.warmup()
predictions, stats = engine.predict(input_data, return_stats=True)
```

### Precontroller

```python
controller = Precontroller(scene_config_path="scenes.json")
commands = controller.evaluate(prediction_result, context)
```

## 🤝 Contribution Guide

Contributions, bug reports, and feature requests are welcome!

## 📄 License

This project is licensed under the MIT License.

---

**Developer**: AI-Assisted Development Team  
**Last Updated**: April 11, 2026
