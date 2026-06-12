# tools/bmi_tool.py

def calculate_bmi(weight_kg, height_cm):
    try:
        height_m = float(height_cm) / 100
        weight_kg = float(weight_kg)

        bmi = weight_kg / (height_m ** 2)

        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal Weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"

        return {
            "bmi": round(bmi, 2),
            "category": category
        }

    except Exception as e:
        return {"error": str(e)}