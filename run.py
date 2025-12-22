# SIMPLE crop model main program
# Author: Mayuanyuan
# Date: 2025-12-20

import os
import pandas as pd
import numpy as np
from datetime import timedelta
import warnings
# ignore all warnings
warnings.filterwarnings("ignore")
# import core functions
from core import (
    simple_crop_model, read_weather, calculate_arid,
    doy_to_date
)


# Main function: run SIMPLE crop model
def main():
    print("=" * 60)
    print("SIMPLE Crop Model - Python Educational Version")
    print("=" * 60)
    print()

    # set working directory to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")
    print()

    # create output folder
    output_dir = "./Output"
    os.makedirs(output_dir, exist_ok=True)
    
    # define output variables
    output_vars = [
        "Day", "DATE", "Tmax", "Tmin", "Radiation", "TT",
        "fSolar", "Biomass", "dBiomass", "HI", "Yield",
        "F_Temp", "F_Heat", "F_Water", "ARID", "I50B", "I50A", "ETO", "MaturityDay"
    ]

    try:
        # 1. read input files
        print("Step 1: Reading input files...")
        management = pd.read_csv("./Input/Simulation Management.csv")  # experiment management file
        treatment = pd.read_csv("./Input/Treatment.csv")  # treatment file
        cultivar = pd.read_csv("./Input/Cultivar.csv")  # cultivar file
        irrigation = pd.read_csv("./Input/Irrigation.csv")  # irrigation file
        soil = pd.read_csv("./Input/Soil.csv")  # soil file
        species_param = pd.read_csv("./Input/Species parameter.csv")  # species parameter file
        print("✓ Input files read successfully")
        print()

        # 2. process column names (replace * with . and trim spaces)
        print("Step 2: Processing column names...")
        for df in [management, treatment, cultivar, irrigation, species_param, soil]:
            # replace * with .
            df.columns = df.columns.str.replace("\\*", ".", regex=True)
            # trim column names
            df.columns = df.columns.str.strip()
        print("✓ Column names processed")
        print()
        
        # 3. filter enabled experiments
        print("Step 3: Filtering experiments...")
        management_enabled = management[management["ON_Off"] == 1]

        if len(management_enabled) == 0:
            print("  ⚠ Warning: No enabled experiments (ON_Off = 1)")
            print("  Using all experiments for demonstration...")
            management_enabled = management.copy()

        print(f"Enabled experiments count: {len(management_enabled)}")
        print()

        # 4. merge data
        print("Step 4: Merging data...")
        print(f"  - treatment records: {len(treatment)}")
        print(f"  - management records: {len(management_enabled)}")
        print(f"  - soil records: {len(soil)}")
        print(f"  - species_param records: {len(species_param)}")

        # unify species names to lowercase (avoid case mismatch)
        treatment["Species."] = treatment["Species."].str.lower()
        management_enabled["Species."] = management_enabled["Species."].str.lower()
        species_param["Species."] = species_param["Species."].str.lower()

        # merge management
        treatment = pd.merge(treatment, management_enabled, on=["Species.", "Exp.", "Trt."], how="inner")
        print(f"  - after merging management: {len(treatment)} records")

        if len(treatment) == 0:
            print("  ✗ Error: No records after merge! Please check if Species., Exp., Trt. column values match")
            print()
            print("  Management example:")
            print(management_enabled[["Species.", "Exp.", "Trt."]].head())
            print()
            print("  Treatment example:")
            print(treatment[["Species.", "Exp.", "Trt."]].head())
            return

        # merge soil
        treatment = pd.merge(treatment, soil, left_on="SoilName", right_on="SoilName.", how="left")
        print(f"  - after merging soil: {len(treatment)} records")

        # merge species_param
        treatment = pd.merge(treatment, species_param, on="Species.", how="left")
        print(f"  - after merging species_param: {len(treatment)} records")

        print(f"✓ Treatment combinations: {len(treatment)}")
        print()
        
        # 5. initialize result storage
        res_daily_all = pd.DataFrame()
        res_summary = []

        # 6. loop through each treatment
        print("Step 5: Running model simulation...")
        print("-" * 60)
        
        for idx, treat in treatment.iterrows():
            exp_name = treat["Exp."]
            trt_name = treat["Trt."]
            crop_name = treat["Species."]
            
            print(f"Treatment {idx + 1}/{len(treatment)}: {crop_name} - {exp_name} - {trt_name}")

            try:
                # 6.1 prepare parameter dictionary
                # get corresponding management record to read Water parameter
                mgmt_row = management_enabled[
                    (management_enabled["Species."] == treat["Species."]) &
                    (management_enabled["Exp."] == treat["Exp."]) &
                    (management_enabled["Trt."] == treat["Trt."])
                ]
                
                water_enabled = True
                if not mgmt_row.empty:
                    water_enabled = str(mgmt_row.iloc[0]["Water"]).lower() in ["yes", "1", "true"]
                
                para = {
                    "Species": {
                        "Tbase": treat["Tbase"],
                        "Topt": treat["Topt"],
                        "RUE": treat["RUE"],
                        "I50maxH": treat["I50maxH"],
                        "I50maxW": treat["I50maxW"],
                        "MaxT": treat["MaxT"],
                        "ExtremeT": treat["ExtremeT"],
                        "S_Water": treat["S_Water"],
                        "CO2_RUE": treat["CO2_RUE"]
                    },
                    "treatment": {
                        "CO2": treat["CO2"],
                        "SowingDate": treat["SowingDate"],
                        "HarvestDate": treat.get("HarvestDate"),
                        "MaxIntercept": treat.get("MaxIntercept", 0.95),
                        "Water": water_enabled,
                        "InitialBio": treat.get("InitialBio", 0),
                        "InitialTT": treat.get("InitialTT", 0),
                        "InitialFsolar": treat.get("InitialFsolar", 0.1)
                    }
                }
                
                # 6.2 get cultivar parameters
                # note: treatment has 'Cultivar', cultivar file has 'Cultivar.'
                cult = cultivar[
                    (cultivar["Species."] == treat["Species."]) &
                    (cultivar["Cultivar."] == treat["Cultivar"])
                ]

                para["Cultivar"] = {
                    "Tsum": cult.iloc[0]["Tsum"],
                    "HI": cult.iloc[0]["HI"],
                    "I50A": cult.iloc[0]["I50A"],
                    "I50B": cult.iloc[0]["I50B"]
                }

                # 6.3 read weather file
                weather_name = f"./Weather/{treat['weather']}"

                # get irrigation data
                irrig_data = irrigation[
                    (irrigation["Species."] == treat["Species."]) &
                    (irrigation["Exp."] == treat["Exp."]) &
                    (irrigation["Trt."] == treat["Trt."])
                ]

                if irrig_data.empty:
                    irrig_data = None

                weather = read_weather(weather_name, irrig_data)

                # 6.4 read latitude and elevation from weather file
                try:
                    with open(f"{weather_name}.WTH", "r") as f:
                        lines = f.readlines()
                        if len(lines) > 3:
                            header = lines[3]
                            lat = float(header[7:16].strip())
                            elev = float(header[25:31].strip())
                        else:
                            lat, elev = 0.0, 0.0
                except:
                    lat, elev = 0.0, 0.0

                # 6.5 convert sowing date
                sowing_date = doy_to_date(para["treatment"]["SowingDate"])
                para["treatment"]["SowingDate"] = sowing_date

                # 6.6 extract weather data after sowing
                sow_idx = weather[weather["IDATE"] == sowing_date].index

                if len(sow_idx) > 0:
                    weather_sow = weather.iloc[sow_idx[0]:].copy().reset_index(drop=True)
                else:
                    print(f"  ⚠ Warning: Sowing date not in weather data range, using all data")
                    weather_sow = weather.copy()

                # 6.7 calculate ARID
                soil_params = {
                    "AWC": treat["AWC"],
                    "DDC": treat["DDC"],
                    "RCN": treat["RCN"],
                    "RZD": treat["RZD"],
                    "WUC": 0.096
                }

                arid_data = calculate_arid(weather_sow, soil_params, lat, elev)

                # 6.8 run crop model
                result = simple_crop_model(para, weather_sow, arid_data)

                # 6.9 add metadata
                result["Crop"] = crop_name
                result["Exp"] = exp_name
                result["Label"] = treat.get("Label", "")
                result["Trt"] = trt_name

                # 6.10 save daily results
                res_daily_all = pd.concat([res_daily_all, result], ignore_index=True)

                # 6.11 save summary results
                final_biomass = result["Biomass"].iloc[-1] if len(result) > 0 else 0
                final_yield = result["Yield"].iloc[-1] if len(result) > 0 else 0

                res_summary.append({
                    "Crop": crop_name,
                    "Exp": exp_name,
                    "Label": treat.get("Label", ""),
                    "Trt": trt_name,
                    "Duration": len(result),
                    "Biomass": round(final_biomass, 0),
                    "Yield": round(final_yield, 0)
                })

                print(f"  ✓ Simulation complete: {len(result)} days, biomass {final_biomass:.0f} kg/ha, yield {final_yield:.0f} kg/ha")
                
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                continue

        print("-" * 60)
        print()

        # 7. display summary results
        print("Step 6: Summary results")
        print("=" * 60)
        res_summary_df = pd.DataFrame(res_summary)
        print(res_summary_df.to_string(index=False))
        print()

        # 8. save results to files
        print("Step 7: Saving results...")

        # 8.1 save daily results
        if not res_daily_all.empty:
            # only keep needed columns
            columns_to_save = [col for col in output_vars if col in res_daily_all.columns]
            daily_file = f"{output_dir}/Res_daily_all.csv"
            res_daily_all.to_csv(daily_file, index=False)
            print(f"✓ Daily results saved: {daily_file}")

        # 8.2 save summary results
        if not res_summary_df.empty:
            summary_file = f"{output_dir}/Res_summary_all.csv"
            res_summary_df.to_csv(summary_file, index=False)
            print(f"✓ Summary results saved: {summary_file}")

        print()
        print("=" * 60)
        print("Model run completed!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"✗ Error: Input file not found - {e}")
        print("Please ensure all necessary input files are in the Input folder")
    except Exception as e:
        print(f"✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
