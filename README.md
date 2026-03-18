# 🥗 DINE: Dish Image Nutrition Estimator

_**Snap a photo, know your nutrition!**_
<br>A deep learning-based web app to estimate the nutritional calories and
<br> macros (Protein, Fat, Carbs) from a photo of food dish

<img src="img/dine-demo_gif_XL.gif" width="500">
<br>
App home: https://dine-frontend-832976041925.asia-northeast1.run.app


## Getting Started
The initial setup.

### Create virtualenv
```bash
# Create new venv
pyenv virtualenv 3.10.6 dine_venv

# Set as local venv
pyenv local dine_venv

# Activate (if not auto)
source dine_venv/bin/activate
```

### Unittest test:
```bash
make clean install test
```

## ENV variables
Defined in two files:
1. `dine/params.py` : Global parameters used in the project. NO SECRETS ALLOWED
2. local `.env` : Local parameters and secrets stored here. DO NOT PUSH TO REPO

## Loading local variables
Make sure that direnv has been installed and `.envrc` file is available in the
<br>project's root directory

Create `.env` file, and add some default parameters
```bash
echo "BASE_DATA_DIR=data/mmfood100k" >> .env
```

Load variables
```bash
# In project root directory, run
direnv allow .
```

If you made some changes, reload variables
```bash
direnv reload .
```

### DB Setup
GCS Bucket location:
```
gs://mmfood/
```

### Run API server
1. Deploy a container in GCP Cloud Run
2. Connect Github repo `master` branch

### Run Frontend
1. Deploy a container in GCP Cloud Run
2. Connect Github repo `master` branch


## Built With
- [Tensorflow]() - Machine Learning & Model Development
- [FastAPI]() - Backend
- [Streamlit]() - Front-end
- [Google Cloud Run]() & [Docker]() - Cloud Deployment
- [Google Cloud Storage]() - Database

## Acknowledgements
Special thanks to our amazing TAs at Le Wagon, espcially Arnaud and Gabriel for
<br>their guidance and roasting when we lost our way in the world of model
<br>and product development

## Team Members
- [Tasha Fahira](www.linkedin.com/in/tashafahira)
- Jose Manuel Garcia Portillo
- Wang Li

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License
