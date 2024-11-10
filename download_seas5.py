import cdsapi

c = cdsapi.Client()

year = list(map(str, list(range(2000, 2024))))
month = list(map(str, list(range(1, 13))))

fields = {
    "hus": "specific_humidity",
    "ta": "temperature",
    "ua": "u_component_of_wind",
    "va": "v_component_of_wind",
    "zg": "geopotential",
}
for sname, field in fields.items():
    c.retrieve(
        "seasonal-monthly-pressure-levels",
        {
            "format": "grib",
            "originating_centre": "ecmwf",
            "system": "51",
            "variable": [field],
            "pressure_level": [
                "500",
                "700",
                "850",
                "925",
                "1000",
            ],
            "product_type": ["monthly_mean"],
            "year": year,
            "month": month,
            "leadtime_month": ["1", "2", "3", "4", "5", "6"],
            "area": [48, -30, -7, 85],
        },
        f"{sname}_plev_seas5_monthly_2000-2023.grib",
    )
