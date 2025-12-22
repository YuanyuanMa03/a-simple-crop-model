# SIMPLE Crop Model - Python Version v2.0

A Python implementation of the SIMPLE (Soil-Plant-Atmosphere Interactions for Model Evaluation and Learning) crop model.

## Description

SIMPLE is a process-based crop model that simulates crop growth and yield based on weather, soil, and management inputs. This Python version maintains the core functionality of the original R implementation while providing improved performance and easier integration with Python-based workflows.

## Features

- Simulates multiple crop types (wheat, maize, rice, soybean, etc.)
- Weather-driven growth simulation
- Water and heat stress responses
- CO2 fertilization effects
- Daily and summary output
- Easy parameter calibration

## Requirements

- Python 3.7+
- pandas
- numpy
- datetime

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/SIMPLE_MODEL_PYv2.0.git
cd SIMPLE_MODEL_PYv2.0
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main model:
```bash
python run.py
```

Adjust parameters:
```bash
python adjust_parameters.py
```

Run machine learning optimization:
```bash
python run_ml_optimization.py
```

## Input Files

- `Input/Simulation Management.csv` - Experiment management settings
- `Input/Treatment.csv` - Treatment definitions
- `Input/Cultivar.csv` - Cultivar parameters
- `Input/Soil.csv` - Soil parameters
- `Input/Species parameter.csv` - Species-specific parameters
- `Input/Irrigation.csv` - Irrigation schedules
- `Weather/*.WTH` - Weather data files

## Output

- `Output/Res_daily_all.csv` - Daily simulation results
- `Output/Res_summary_all.csv` - Summary statistics for all simulations

## Model Structure

- `core.py` - Core model functions
- `run.py` - Main execution script
- `adjust_parameters.py` - Parameter adjustment utilities
- `run_ml_optimization.py` - Machine learning parameter optimization

## Citation

If you use this model in your research, please cite:

[Add citation information]

## License

[Add license information]

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.