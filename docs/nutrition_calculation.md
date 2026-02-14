Regarding the calculation of scale_factor and the nutritional values for a 100g dish:
I treat each dish as a whole and proportionally scale its nutritional values to estimate the nutrition per 100g.
1. First, calculate the total weight of each dish:
    Sum portion_size values.

2. Normalize to 100g → calculate scale_factor:
    scale_factor = 100 / (total weight of the dish)

3. Calculate the standardized nutritional values:
    Multiply each nutrient in the nutritional_profile by the scale_factor.
