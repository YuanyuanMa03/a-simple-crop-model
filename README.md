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
- Support for multiple weather formats (.WTH and .csv)
- Aridity index calculations
- Temperature and water stress factors

## Requirements

- Python 3.7+
- pandas
- numpy
- datetime

## Installation

1. Clone this repository:
```bash
git clone https://github.com/YuanyuanMa03/SIMPLE_MODEL_PYv2.0.git
cd SIMPLE_MODEL_PYv2.0
```

2. Install dependencies:
```bash
pip install pandas numpy
```

## Usage

Run the main model:
```bash
python run.py
```

The model will automatically:
- Read input files from the `Input/` directory
- Load weather data from the `Weather/` directory
- Generate output files in the `Output/` directory

## Input Files

### Required Input Files:
- `Input/Simulation Management.csv` - Experiment management settings
- `Input/Treatment.csv` - Treatment definitions
- `Input/Cultivar.csv` - Cultivar parameters
- `Input/Soil.csv` - Soil parameters
- `Input/Species parameter.csv` - Species-specific parameters
- `Input/Irrigation.csv` - Irrigation schedules

### Weather Data:
- `Weather/*.WTH` - Weather data files in WTH format
- `Weather/*.csv` - Weather data files in CSV format (alternative)

The model includes 50+ weather stations covering various regions (Arizona, Florida, Georgia, Ohio, etc.) and international locations (Australia, Brazil, etc.).

## Output

- `Output/Res_daily_all.csv` - Daily simulation results including:
  - Day, DATE, Tmax, Tmin, Radiation
  - Growing degree days (TT), solar interception (fSolar)
  - Biomass accumulation, daily biomass change
  - Harvest index, yield predictions
  - Stress factors (F_Temp, F_Heat, F_Water)
  - Aridity index (ARID), evapotranspiration (ETO)
  - Maturity timing information

- `Output/Res_summary_all.csv` - Summary statistics for all simulations

## Model Structure

- `core.py` - Core model functions including:
  - Weather data processing (`read_weather()`)
  - Aridity calculations (`calculate_arid()`)
  - Main simulation engine (`simple_crop_model()`)
  - Date utilities (`doy_to_date()`)

- `run.py` - Main execution script that:
  - Orchestrates the simulation workflow
  - Handles input/output file management
  - Processes multiple experiments
  - Generates comprehensive output reports

## Key Features

- **Multi-format support**: Handles both .WTH and .csv weather file formats
- **Comprehensive simulation**: Models temperature, water, and heat stress impacts
- **Flexible management**: Supports various cultivars, treatments, and irrigation schedules
- **Robust output**: Detailed daily tracking and summary statistics
- **Educational focus**: Clear code structure for learning and modification

## License

This project is provided for educational and research purposes.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Version

Version 2.0 - Python Implementation
Author: Mayuanyuan
Date: 2025-12-20