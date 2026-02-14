const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");


imageInput.addEventListener("change", function() {
    const file = this.files[0];
    if (file) {
        preview.src = URL.createObjectURL(file);
        preview.style.display = "block";
    }
});


//  real analyze
async function analyzeFood() {
    const file = imageInput.files[0];
    const portion = document.getElementById("portionInput").value;

    if (!file) {
        alert("Please upload a photo.");
        return;
    }

    const formData = new FormData();
    formData.append("image", file);
    formData.append("portion", portion);

    const response = await fetch("http://localhost:8000/predict", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    displayResult(data, portion);
}


// for test
// function analyzeFood() {

//     const fakeData = {
//         dish: "ramen",
//         confidence: 0.92,
//         portion: 200,
//         nutrition: {
//             calories: 520,
//             protein_g: 18,
//             carbs_g: 65,
//             fat_g: 20
//         }
//     };

//     displayResult(fakeData);
// }


function displayResult(data) {
    document.getElementById("resultCard").style.display = "block";

    document.getElementById("detectedFood").innerText =
        `Detected food: ${data.dish}`;

    document.getElementById("nutritionTitle").innerText =
        `Nutrition for ${data.portion} g`;

    document.getElementById("calories").innerText =
        data.nutrition.calories + " kcal";

    document.getElementById("protein").innerText =
        data.nutrition.protein_g + " g";

    document.getElementById("fat").innerText =
        data.nutrition.fat_g + " g";

    document.getElementById("carbs").innerText =
        data.nutrition.carbs_g + " g";
}
