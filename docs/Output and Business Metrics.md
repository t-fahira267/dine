# Output (Y):

**4 Nutrition Values:**

- Calories (kcal)
- Protein (gr)
- Fat (gr)
- Carbohydrate (gr)

## **MVP 1: Food Label + Standardized portion + Standardized ingredients = Discrete output —> DONE (model)**

| dish_name (y1) | **nutritional_profile (Y)** |
| --- | --- |
| **banana** | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |
| **sushi** | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |
| **sushi** | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |

## **MVP 2: Food Label + Free portion + Standardized ingredients = Continuous**

| dish_name (y1) | portion_size_gr (y2) | **nutritional_profile (Y)** |
| --- | --- | --- |
| banana | ["banana”:100] | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |
| sushi | [”rice”:**10**, “fish”:**5**] | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |
| sushi | [”rice”:**20**, “fish”:**10**] | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |

## **MVP 3: Food Label + Free portion + Free ingredients = Continuous**

| dish_name (y1) | portion_size_gr (y2) | **nutritional_profile (Y)** |
| --- | --- | --- |
| banana | ["banana”:100] | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |
| sushi | [”rice”:10, “**salmon**”:5] | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |
| sushi | [”rice”:20, “**tuna**”:10] | {"fat_g":15.0,"protein_g":25.0,"calories_kcal":450,"carbohydrate_g":60.0} |

---
# Business metric

Estimation of **continuous value** of Y

## Mean Absolute Error (MAE)

## Mean Absolute Percentage Error (MAPE)
