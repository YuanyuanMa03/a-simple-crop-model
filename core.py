# SIMPLE crop model core functions
# Author: Mayuanyuan
# Date: 2025-12-20

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math
import warnings
# ignore warnings
warnings.filterwarnings("ignore")

# Convert DOY format to date object
# Format: YYDDD -> date
# Example: 18150 -> 2018-05-30
def doy_to_date(date_str):
    # ensure 5-digit string
    date_str = f"{int(date_str):05d}"

    # extract year and day of year
    year = int(date_str[:2])
    doy = int(date_str[2:])

    # determine century
    if year > 20:
        year += 1900
    else:
        year += 2000

    # convert to date
    date = datetime(year, 1, 1) + timedelta(days=doy - 1)
    return date


# Read weather file and process data
def read_weather(weather_name, irrigation=None):
    # try to read .WTH or .csv file
    if os.path.exists(f"{weather_name}.WTH"):
        # WTH file uses whitespace separation
        weather = pd.read_csv(f"{weather_name}.WTH", skiprows=4, sep=r"\s+")
    elif os.path.exists(f"{weather_name}.csv"):
        weather = pd.read_csv(f"{weather_name}.csv")
    else:
        raise FileNotFoundError(f"Weather file not found: {weather_name}")

    # ensure correct column names
    if weather.columns[0] != "DATE":
        weather.columns.values[0] = "DATE"

    # convert date format
    weather["DATE"] = weather["DATE"].apply(lambda x: f"{int(x):05d}")
    weather["IDATE"] = weather["DATE"].apply(doy_to_date)

    # convert irrigation dates
    if irrigation is not None and not irrigation.empty:
        irrigation["IrrDate"] = irrigation["IrrDate"].apply(doy_to_date)

    # clean non-numeric characters from data
    def clean_numeric(series):
        # clean non-numeric characters in numeric columns
        if not pd.api.types.is_numeric_dtype(series):
            series = series.astype(str).str.replace("[^0-9.-]", "", regex=True)
            series = pd.to_numeric(series, errors="coerce")
        return series

    weather["TMAX"] = clean_numeric(weather["TMAX"])
    weather["TMIN"] = clean_numeric(weather["TMIN"])
    weather["SRAD"] = clean_numeric(weather["SRAD"])
    weather["RAIN"] = clean_numeric(weather["RAIN"])

    # add irrigation to rainfall
    if irrigation is not None and not irrigation.empty:
        for _, irr_row in irrigation.iterrows():
            date_irri = irr_row["IrrDate"]
            amount = irr_row["IrrAmount"]

            # find corresponding date and add rainfall
            mask = weather["IDATE"] == date_irri
            if mask.any():
                weather.loc[mask, "RAIN"] += amount

    return weather


# Calculate daily effective thermal time (Degree Day)
# Formula: dTT = max(Tmean - Tbase, 0)
def calculate_dtt(tmean, tbase):
    return max(tmean - tbase, 0)


# Calculate daily biomass increment
# Formula: dBiomass = 10 * RUE * fSolar * SRAD * F_CO2 * F_Temp * min(F_Water, F_Heat)
def calculate_daily_biomass(f_solar, srad, f_co2, f_temp, f_water, f_heat, rue):
    return 10 * rue * f_solar * srad * f_co2 * f_temp * min(f_water, f_heat)


# Temperature response function
# When Tmean >= Topt: response = 1 (optimal)
# Otherwise: linear interpolation: (Tmean - Tbase) / (Topt - Tbase)
def temperature_response(tmean, tbase, topt):
    if tmean >= topt:
        return 1.0
    else:
        return max((tmean - tbase) / (topt - tbase), 0)


# CO2 response function
# Simulate CO2 fertilization effect
def co2_response(co2, co2_rue):
    if co2 >= 700:
        return 1 + co2_rue * 350 / 100
    else:
        return max((co2_rue * co2 * 0.01 + 1 - 0.01 * 350 * co2_rue), 1)


# Water stress response function
# Calculate water stress based on ARID index
def water_response(arid, s_water):
    return max(0, 1 - s_water * arid)


# Heat stress response function
# When Tmax <= MaxT: no stress (1)
# When Tmax > ExtremeT: complete stress (0)
# Linear decrease in between
def heat_response(tmax, max_t, extreme_t):
    if tmax <= max_t:
        return 1.0
    elif tmax > extreme_t:
        return 0.0
    else:
        return max(1 - (tmax - max_t) / (extreme_t - max_t), 0)


# Priestley-Taylor ET calculation
# Simplified ET0 calculation
def priestley_taylor_pet(albedo, srad, tmax, tmin, xhlai):
    td = 0.6 * tmax + 0.4 * tmin

    if xhlai <= 0:
        albedo = albedo
    else:
        albedo = 0.23 - (0.23 - albedo) * math.exp(-0.75 * xhlai)

    slang = srad * 23.923
    eeq = slang * (2.04e-4 - 1.83e-4 * albedo) * (td + 29.0)

    pt = eeq * 1.1

    if tmax > 35:
        pt = eeq * ((tmax - 35.0) * 0.05 + 1.1)
    elif tmax < 5.0:
        pt = eeq * 0.01 * math.exp(0.18 * (tmax + 20))

    return max(pt, 0.0001)


# Calculate ARID drought index
def calculate_arid(weather, soil_params, lat, elev):
    # extract required columns
    dat = weather[["SRAD", "TMAX", "TMIN", "RAIN"]].copy()
    dat["DEWPOINT"] = weather["TMIN"]
    dat["WINDSPEED"] = 1.0
    dat["DOY"] = weather["DATE"].apply(lambda x: int(x[2:]))
    dat["YEAR"] = weather["IDATE"].dt.year

    rain = dat["RAIN"].values

    # soil parameters
    awc = soil_params.get("AWC", 0.13)
    ddc = soil_params.get("DDC", 0.55)
    rcn = soil_params.get("RCN", 65)
    rzd = soil_params.get("RZD", 400)
    wuc = soil_params.get("WUC", 0.096)

    # initialize arrays
    n_days = len(dat)
    eto = np.zeros(n_days)
    wbd = np.zeros(n_days)
    wat = np.zeros(n_days)
    arid = np.zeros(n_days)

    # constants
    lat_rad = lat * math.pi / 180
    psc = 0.665e-3 * 101.3 * ((293 - 0.0065 * elev) / 293) ** 5.26
    
    for i in range(n_days):
        # calculate ET0 (FAO-56 method)
        year = dat["YEAR"].iloc[i]
        days_in_year = 366 if (year % 4 == 0) else 365

        ws2 = dat["WINDSPEED"].iloc[i] * 4.87 / math.log(67.8 * 10 - 5.42)

        # saturation vapor pressure
        es = (0.6108 * math.exp(17.27 * dat["TMAX"].iloc[i] / (dat["TMAX"].iloc[i] + 237.3)) +
              0.6108 * math.exp(17.27 * dat["TMIN"].iloc[i] / (dat["TMIN"].iloc[i] + 237.3))) / 2

        # vapor pressure curve slope
        tavg = (dat["TMAX"].iloc[i] + dat["TMIN"].iloc[i]) / 2
        slope = (0.6108 * math.exp(17.27 * tavg / (tavg + 237.3)) * 4098) / (tavg + 237.3) ** 2

        # shortwave radiation
        swr = (1 - 0.23) * dat["SRAD"].iloc[i]

        # extraterrestrial radiation
        irdes = 1 + 0.033 * math.cos(2 * math.pi * dat["DOY"].iloc[i] / days_in_year)
        sd = 0.409 * math.sin(2 * math.pi * dat["DOY"].iloc[i] / days_in_year - 1.39)
        ssa = math.acos(max(min(-math.tan(lat_rad) * math.tan(sd), 1), -1))
        extra = (24 * 60 * 0.082 / math.pi * irdes *
                 (ssa * math.sin(lat_rad) * math.sin(sd) +
                  math.cos(lat_rad) * math.cos(sd) * math.sin(ssa)))

        csr = (0.75 + 2e-5 * elev) * extra
        rrad = dat["SRAD"].iloc[i] / csr

        # actual vapor pressure
        ea = 0.6108 * math.exp(17.27 * dat["DEWPOINT"].iloc[i] / (dat["DEWPOINT"].iloc[i] + 237.3))

        # longwave radiation
        lwr = (4.903e-9 * ((dat["TMAX"].iloc[i] + 273.16) ** 4 +
                           (dat["TMIN"].iloc[i] + 273.16) ** 4) / 2 *
               (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * rrad - 0.35))

        nrad = swr - lwr

        # calculate ET0
        eto[i] = ((0.408 * slope * nrad + psc * (900 / (tavg + 273)) * ws2 * (es - ea)) /
                  (slope + psc * (1 + 0.34 * ws2)))

        # use Priestley-Taylor method
        petmodel = "PT"
        if petmodel == "PT":
            albedo = 0.23
            xhlai = -99
            eto[i] = priestley_taylor_pet(albedo, dat["SRAD"].iloc[i],
                                          dat["TMAX"].iloc[i], dat["TMIN"].iloc[i], xhlai)

        # calculate ARID
        if rain[i] > 0.2 * (25400 / rcn - 254):
            ro = (rain[i] - 0.2 * (25400 / rcn - 254)) ** 2 / (rain[i] + 0.8 * (25400 / rcn - 254))
        else:
            ro = 0

        cwbd = rain[i] - ro

        if i == 0:
            w_at = rzd * awc  # initial soil water content
        else:
            w_at = wat[i-1]

        wbd[i] = cwbd + w_at

        if wbd[i] / rzd > awc:
            dr = rzd * ddc * (wbd[i] / rzd - awc)
        else:
            dr = 0

        wad = wbd[i] - dr
        tr = min(wuc * rzd * wad / rzd, eto[i])
        wat[i] = wad - tr
        arid[i] = 1 - tr / eto[i]
    
    return pd.DataFrame({
        "DATE": weather["IDATE"],
        "ARID": arid,
        "ETO": eto
    })


# SIMPLE crop model main function
def simple_crop_model(para, weather, arid_data):
    # read parameters
    # species parameters
    species = para["Species"]
    tbase = species["Tbase"]
    topt = species["Topt"]
    rue = species["RUE"]
    i50max_h = species["I50maxH"]
    i50max_w = species["I50maxW"]
    max_t = species["MaxT"]
    extreme_t = species["ExtremeT"]
    s_water = species["S_Water"]
    co2_rue = species["CO2_RUE"]

    # cultivar parameters
    cultivar = para["Cultivar"]
    tsum = cultivar["Tsum"]
    hip = cultivar["HI"]
    i50a = cultivar["I50A"]
    i50b = cultivar["I50B"]

    # management parameters
    treatment = para["treatment"]
    init_fsolar = treatment["InitialFsolar"]
    fsolar_max = treatment.get("MaxIntercept", 0.95)
    sowing_date = treatment["SowingDate"]
    harvest_date = treatment.get("HarvestDate")
    co2 = treatment["CO2"]
    water_stress = treatment.get("Water", True)
    init_bio = treatment.get("InitialBio", 0)
    init_tt = treatment.get("InitialTT", 0)

    # maximum simulation days
    fharv = 400

    # if harvest date specified, truncate data
    if harvest_date is not None and not pd.isna(harvest_date):
        harvest_date = doy_to_date(harvest_date)
        dua = (harvest_date - sowing_date).days + 1
        weather = weather.iloc[:dua].copy()
        arid_data = arid_data.iloc[:dua].copy()

    # determine simulation days
    stop_day = min(len(weather), fharv)
    weather = weather.iloc[:stop_day].copy()
    arid_data = arid_data.iloc[:stop_day].copy()

    # initialize result arrays
    days = np.arange(1, stop_day + 1)
    result = pd.DataFrame({
        "Day": days,
        "DATE": weather["IDATE"].iloc[:stop_day],
        "ETO": np.zeros(stop_day),
        "TT": np.zeros(stop_day),
        "Biomass": np.zeros(stop_day),
        "Tmax": weather["TMAX"].iloc[:stop_day],
        "Tmin": weather["TMIN"].iloc[:stop_day],
        "Radiation": weather["SRAD"].iloc[:stop_day],
        "HI": np.full(stop_day, hip),
        "ARID": arid_data["ARID"].iloc[:stop_day]
    })

    # calculate environmental stress factors
    result["F_Water"] = [water_response(arid, s_water) for arid in result["ARID"]]
    if not water_stress:
        result["F_Water"] = 1.0

    result["dETO"] = arid_data["ETO"].iloc[:stop_day]
    result["F_Heat"] = [heat_response(tmax, max_t, extreme_t) for tmax in result["Tmax"]]
    result["Tmean"] = (result["Tmin"] + result["Tmax"]) / 2
    result["F_Temp"] = [temperature_response(tmean, tbase, topt) for tmean in result["Tmean"]]
    result["F_CO2"] = co2_response(co2, co2_rue)

    # calculate thermal time
    result["dTT"] = [calculate_dtt(tmean, tbase) for tmean in result["Tmean"]]
    result["TT"] = np.cumsum(result["dTT"]) - result["dTT"] + init_tt
    result["Yield"] = np.zeros(stop_day)

    # initialize light interception parameters
    result["I50A"] = np.full(stop_day, i50a)
    result["I50B"] = np.full(stop_day, i50b)

    # water stress effect on light interception
    f_solar_water = result["F_Water"].copy()
    f_solar_water[f_solar_water > 0.1] = 1
    f_solar_water[f_solar_water <= 0.1] = f_solar_water[f_solar_water <= 0.1] + 0.9
    result["fSolar_water"] = f_solar_water

    # light interception dynamics
    result["fSolar"] = np.full(stop_day, init_fsolar)

    maturity_day2 = stop_day

    # daily simulation
    # remove math import, use numpy for consistency
    for day in range(1, stop_day):
        # calculate light interception (double logistic curve)
        tt = result["TT"].iloc[day]
        i50a_prev = result["I50A"].iloc[day-1]
        i50b_prev = result["I50B"].iloc[day-1]

        # use numpy.exp for numerical precision consistency
        f_solar1 = min(1, fsolar_max / (1 + np.exp(-0.01 * (tt - i50a_prev))))
        f_solar2 = min(1, fsolar_max / (1 + np.exp(0.01 * (tt - (tsum - i50b_prev)))))

        result.loc[day, "fSolar"] = min(f_solar1, f_solar2) * min(result["fSolar_water"].iloc[day-1], 1)

        # I50B dynamic adjustment (stress affected)
        f_water_prev = result["F_Water"].iloc[day-1]
        f_heat_prev = result["F_Heat"].iloc[day-1]

        di50b1 = i50b_prev + i50max_w * (1 - f_water_prev)
        di50b2 = i50b_prev + i50max_h * (1 - f_heat_prev)
        result.loc[day, "I50B"] = max(max(0, di50b1), max(0, di50b2))

        # check for premature senescence
        # fully match R version logic, add tolerance for floating point errors
        if (result["fSolar"].iloc[day] < result["fSolar"].iloc[day-1] and
            result["fSolar"].iloc[day] <= 0.005 + 1e-6):
            maturity_day2 = day  # fix: consistent with R version
            break

    # determine maturity
    maturity_day1 = len(result[result["TT"] <= tsum])
    maturity_day = min(maturity_day1, maturity_day2)

    result["MaturityDay"] = maturity_day
    result = result.iloc[:maturity_day].copy()

    if maturity_day <= 1:
        return result

    # calculate biomass and yield
    result["ETO"] = np.cumsum(result["dETO"]) - result["dETO"]

    # calculate daily biomass
    daily_biomass = []
    for idx, row in result.iterrows():
        db = calculate_daily_biomass(
            row["fSolar"], row["Radiation"], row["F_CO2"],
            row["F_Temp"], row["F_Water"], row["F_Heat"], rue
        )
        daily_biomass.append(db)

    result["dBiomass"] = daily_biomass
    result["Biomass"] = np.cumsum(result["dBiomass"]) - result["dBiomass"] + init_bio
    result["Yield"] = result["Biomass"] * hip

    return result
