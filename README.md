# DINE: Dish Image Nutrition Estimator
Computer vision for your nutrition

- Project name: `dine`
- Description: Estimate nutritional information from image of a meal
- Data Source: https://huggingface.co/datasets/Codatta/MM-Food-100K
- Type of analysis: Computer Vision

---

# Startup the project

The initial setup.

Create virtualenv and install the project:
```bash
sudo apt-get install virtualenv python-pip python-dev
deactivate; virtualenv ~/venv ; source ~/venv/bin/activate ;\
    pip install pip -U; pip install -r requirements.txt
```

Unittest test:
```bash
make clean install test
```

Check for dine in github.com/{group}. If your project is not set please add it:

Create a new project on github.com/{group}/dine
Then populate it:

```bash
##   e.g. if group is "{group}" and project_name is "dine"
git remote add origin git@github.com:{group}/dine.git
git push -u origin master
git push -u origin --tags
```

Functionnal test with a script:

```bash
cd
mkdir tmp
cd tmp
dine-run
```

# Install

Go to `https://github.com/{group}/dine` to see the project, manage issues,
setup you ssh public key, ...

Create a python3 virtualenv and activate it:

```bash
sudo apt-get install virtualenv python-pip python-dev
deactivate; virtualenv -ppython3 ~/venv ; source ~/venv/bin/activate
```

Clone the project and install it:

```bash
git clone git@github.com:{group}/dine.git
cd dine
pip install -r requirements.txt
make clean install test                # install and test
```
Functionnal test with a script:

```bash
cd
mkdir tmp
cd tmp
dine-run
```

# GCP

## Bucket Location

```
gs://dine-mmfood/mmfood100k/v1/
```

Region: asia-northeast1 (Tokyo)

## Dataset Structure

```
mmfood100k/v1/
  images/
    sushi/
    ramen/
  labels.csv
  candidates.csv
```

**`images/`**

Contains downloaded images grouped by canonical dish label.

```
images/sushi/000001.jpg
images/ramen/000001.jpg
```

**`labels.csv`**

Format:
```
image_path	label
images/sushi/000001.jpg	sushi
images/ramen/000001.jpg	ramen
```

Notes:

- image_path is relative to the root of v1/

- Labels are lowercase and standardized

**`candidates.csv`**

Cleaned up .csv data that will serve as the unique source of truth

## How to upload to GCP

1. Login and configure the project

```
gcloud auth login
```

2. Check you can reach the bucket

```
gsutil ls gs://mmfood
```

3. Run makefile command (this will cleanup the HuggingFace dataset, download it locally and upload it to GCS)
```
make dataset
```


## Inference Pipeline

### MVP
```mermaid
flowchart LR
  U([User]) -->|Input image and portion size| UI[UI]
  UI -->|POST image and portion size| API[Server API]

  subgraph ML_Pipeline
    direction LR
    P[Preprocessing]
    M[Model]
    P -->|Clean image| M
  end

  API -->|Send raw image| P
  M -->|Dish prediction| API

  API -->|Lookup dish nutrition| CSV[(Nutrition CSV mapping)]
  CSV -->|Nutrition per dish| API

  API -->|Compute nutrition using portion| CALC[Compute nutrition]
  CALC -->|Final response| UI

  UI -->|Show output| U
