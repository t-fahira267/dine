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
