# A Simple Crop Model

A Python implementation of the SIMPLE (Soil-Plant-Atmosphere Interactions for Model Evaluation and Learning) crop model.

SIMPLE 作物模型的 Python 实现。SIMPLE（土壤-植物-大气交互模型评估与学习）是一个基于过程的作物模型。

---

[English](#english) | [中文](#中文)

---

<a id="english"></a>

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
git clone https://github.com/YuanyuanMa03/a-simple-crop-model.git
cd a-simple-crop-model
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
- `Input/Simulation Management.csv` — Experiment management settings
- `Input/Treatment.csv` — Treatment definitions
- `Input/Cultivar.csv` — Cultivar parameters
- `Input/Soil.csv` — Soil parameters
- `Input/Species parameter.csv` — Species-specific parameters
- `Input/Irrigation.csv` — Irrigation schedules

### Weather Data:
- `Weather/*.WTH` — Weather data files in WTH format
- `Weather/*.csv` — Weather data files in CSV format (alternative)

The model includes 50+ weather stations covering various regions (Arizona, Florida, Georgia, Ohio, etc.) and international locations (Australia, Brazil, etc.).

## Output

- `Output/Res_daily_all.csv` — Daily simulation results including:
  - Day, DATE, Tmax, Tmin, Radiation
  - Growing degree days (TT), solar interception (fSolar)
  - Biomass accumulation, daily biomass change
  - Harvest index, yield predictions
  - Stress factors (F_Temp, F_Heat, F_Water)
  - Aridity index (ARID), evapotranspiration (ETO)
  - Maturity timing information

- `Output/Res_summary_all.csv` — Summary statistics for all simulations

## Model Structure

- `core.py` — Core model functions:
  - Weather data processing (`read_weather()`)
  - Aridity calculations (`calculate_arid()`)
  - Main simulation engine (`simple_crop_model()`)
  - Date utilities (`doy_to_date()`)

- `run.py` — Main execution script:
  - Orchestrates the simulation workflow
  - Handles input/output file management
  - Processes multiple experiments
  - Generates comprehensive output reports

## License

This project is provided for educational and research purposes.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

<a id="中文"></a>

## 简介

SIMPLE 基于气象、土壤和管理输入来模拟作物生长与产量。本 Python 版本保留了原始 R 实现的核心功能，同时提供了更好的性能以及与 Python 生态的便捷集成。

## 功能特性

- 支持多种作物类型（小麦、玉米、水稻、大豆等）
- 气象驱动的生长模拟
- 水分胁迫与高温胁迫响应
- CO2 施肥效应
- 逐日输出与汇总输出
- 支持多种气象数据格式（.WTH 和 .csv）
- 干旱指数计算
- 温度与水分胁迫因子

## 环境要求

- Python 3.7+
- pandas
- numpy
- datetime

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/YuanyuanMa03/a-simple-crop-model.git
cd a-simple-crop-model
```

2. 安装依赖：
```bash
pip install pandas numpy
```

## 使用方法

运行主模型：
```bash
python run.py
```

模型将自动完成以下操作：
- 从 `Input/` 目录读取输入文件
- 从 `Weather/` 目录加载气象数据
- 在 `Output/` 目录生成输出文件

## 输入文件

### 必需输入文件：
- `Input/Simulation Management.csv` — 模拟管理设置
- `Input/Treatment.csv` — 处理定义
- `Input/Cultivar.csv` — 品种参数
- `Input/Soil.csv` — 土壤参数
- `Input/Species parameter.csv` — 物种参数
- `Input/Irrigation.csv` — 灌溉计划

### 气象数据：
- `Weather/*.WTH` — WTH 格式的气象数据文件
- `Weather/*.csv` — CSV 格式的气象数据文件（备选）

模型内置 50+ 个气象站点，覆盖美国多个地区（亚利桑那、佛罗里达、佐治亚、俄亥俄等）及国际站点（澳大利亚、巴西等）。

## 输出

- `Output/Res_daily_all.csv` — 逐日模拟结果，包括：
  - 天数、日期、最高温、最低温、辐射
  - 有效积温 (TT)、太阳辐射截获 (fSolar)
  - 生物量累积、日生物量变化
  - 收获指数、产量预测
  - 胁迫因子 (F_Temp, F_Heat, F_Water)
  - 干旱指数 (ARID)、蒸散量 (ETO)
  - 成熟时间信息

- `Output/Res_summary_all.csv` — 所有模拟的汇总统计

## 模型结构

- `core.py` — 核心模型函数：
  - 气象数据处理 (`read_weather()`)
  - 干旱指数计算 (`calculate_arid()`)
  - 主模拟引擎 (`simple_crop_model()`)
  - 日期工具 (`doy_to_date()`)

- `run.py` — 主执行脚本：
  - 编排模拟流程
  - 管理输入/输出文件
  - 处理多个试验
  - 生成综合输出报告

## 许可证

本项目仅供教育和研究用途。

## 贡献

欢迎提交 Pull Request。如有重大修改，请先开 Issue 进行讨论。

## 作者

Author: Mayuanyuan
Date: 2025-12-20
