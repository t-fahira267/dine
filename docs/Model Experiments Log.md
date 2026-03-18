# DINE: Nutrition Prediction Experiments Log

**Goal**: Take a photo of food → predict fat, protein, carbs, and calories.
**Data**: 4,024 photos across 12 food types (pizza, ramen, fried chicken, apple, etc.)

## Baseline
What: Identify the food, then return the average nutrition values for that food class from the training data. No per-image prediction at all.
Result: Food identification: 94.4% accurate. Nutrition: okay but limited (eg. every apple photo gets the exact same prediction regardless of how big it is)
Conclusion: Even if we got food identification perfectly right, it would only reduce nutrition error by ~10% since we are working with averages. We need the model to estimate nutrition per image.

## Experiment 1 (v1.0) ->  Predicting nutrition from the photo
What: Instead of looking up averages, we train a small "prediction layer" (Regression) on top to estimate nutrition directly from the image.
Result: Worse than baseline on most metrics. The model essentially ignored fat and protein and focused almost entirely on calories.
Conclusion: Calories are measured in the hundreds (e.g. 400 kcal), while fat and protein are measured in tens (e.g. 20g). When we train with those raw numbers, the model sees calorie errors as ~100× more important vs the other nutrients.

## Experiment 2 (v2.0) ->  Rescale the numbers so all nutrients are treated equally
What: Before training, we use StandardScaler to rescale all 4 nutrients to the same scale. This fixes the imbalance from v1.0: now a 20% error on fat "hurts" just as much as a 20% error on calories during training.
Result: All error metrics improved vs v1.0. Interestingly enough, when StandardScaler equalized the loss, calories Median MAPE got worse (18.8% → 22.8%) while fat/protein/carbs all improved.
Conclusion: It feels the model couldn't maintain calorie accuracy AND improve the others simultaneously. Fat, protein, and carbs are all grams so they share similar distributions. Calories is a fundamentally different unit. Also we found out in class that we can calculate it mathematically using the other 3 nutrients (calories = 9xfat + 4xcarbs + 4xprotein). Calories aren't independent so we might as well remove them from the regression.

## Experiment 3 (v3.0) ->  Stop predicting calories directly; calculate them from the other three
What: We have the formula (shown above). So instead of predicting all 4, predict only fat/protein/carbs and derive calories from those.
Result: Best improvement so far. All metrics improved ~8% vs v2.0. But we realized that v3.0 had plateaued at epoch 14 even though its actual errors (5–9g off) still had room to improve.
Conclusion: We realized MSE was squishing small errors so much that the model thought it was done. Also, we were evaluating with MAE but training with MSE. Basically, the model was being trained with one goal and judged by a different one.

## Experiment 4 (v4.0) ->  Change how the model measures its own mistakes during training
What: Switch the training error function from MSE (mean squared error) to MAE (mean absolute error).  With MSE, we square the error. So if we're 0.3g off, the penalty is 0.3² = 0.09. So as the model gets closer to the right answer, the signal telling it "keep improving" almost disappears.
With MAE, the penalty is just the raw error. 0.3g off → penalty is 0.3. The signal stays proportional to the mistake.
Result: All metrics improved again (~10% MAE reduction vs v3.0). First model to beat the baseline on every single metric (both MAE and MAPE). Still, we realized that heavy/large-portion foods (eg. fried_chicken_and_fries: -81.9 kcal, ramen: -69.9 kcal) were consistently under-predicted. Light foods (eg. apple: +33.9 kcal) were over-predicted.
Conclusion: The model learned to recognize images in general, so it is good enough to identify what food it is, but not to notice visual cues about how much there is or how it's prepared (eg. things like how full the plate is, how thick the portion looks, or how saucy it is). To pick up on those details, we need to fine-train it.

## Experiment 5 (v5.0) ->  Fine-tune the model
What: Up to now, the image understanding part of the model was completely frozen so it used generic visual features from ImageNet training (cars, dogs, furniture…). In v5.0 we "unfroze" the top layers and let them adapt specifically to food photos during training.
Result: Small but consistent improvement across all metrics (~2% better MAE). However, we saw signs of mild overfitting
Conclusion: Do some data augmentation would help with this.

NOTE: Since fine-tuning takes longer (1h 20 min or so), I will be doing first experiments that dont need fine-tuning like using log-transform on targets to try and deal with the overestimation of low-value nutrients (eg. apple's fat_g).

NOTE 2: All models are uploaded in GCS under the models folder so we can point our api to them at any time

## Experiment 6 (v6.0) -> Train the food identifier and nutrition predictor jointly (shared layer)
What: Instead of two completely separate models (one that identifies food, one that predicts nutrition), we make them share a common "thinking layer" in the middle. The idea is that learning to identify food and learning to predict nutrition can help each other.
Result: Worse than v4.0 on every metric. The classifier learns very quickly (99%+ accuracy in just a few epochs). The regressor takes much longer. Since they share the same layer, once the classifier is done, it stops sending meaningful update signals to that layer. The regressor is still trying to learn but it has to work with a layer that was already shaped by the classifier, so it can't reshape it enough for its own needs.
Conclusion: Giving each task its own dedicated layer works better than forcing them to share.

## Experiment 7 (v7.0) -> Log-transform targets before training
What: Before training, apply log to all nutrition values. This compresses large values (a 500 kcal meal and a 1000 kcal meal become closer together) and stretches small values (0.3g fat and 1g fat become more distinguishable). After predicting, we reverse the transform to get back real units.
The reason is that from v4.0 and v5.0 we saw the model systematically over-predicted low-value foods (eg. it predicted ~5g fat for an apple that has 0.3g). The model was treating "being 5g off on a 0.3g item" the same as "being 5g off on a 30g item." Log-transform makes the model care more proportionally about small values.
Result: All metrics improved vs v4.0 (we are leaving v5.0 aside for a bit since it takes longer to run). For example, apple fat bias dropped from +1.49g to +0.52g (65% better). In fact, v7.0 on frozen features was competitive with v5.0 which used full fine-tuning (it had similar accuracy in 20 min vs 1h 20 min).
Conclusion: Log-transform is a clear winner and should be included in all future experiments. Next we have been seeing some imbalance in the data, we will aim to tackle that.

## Experiment 8 (v8.0) -> Give more weight to underrepresented food classes during training
What: Our dataset is imbalanced; we have ~700 photos of fried chicken but only ~139 of french fries. We added class weights so that a mistake on a rare food (french fries) counts 5× more than a mistake on a common food (fried chicken) during training.
Result: Classification accuracy unchanged (still 94.2%). Nutrition MAE got worse on 3 out of 4 nutrients. All Median MAPEs got worse.
Conclusion: The classifier was already doing well on all classes including rare ones (french fries: 100% accuracy). The imbalance wasn't actually causing problems, so fixing it didn't help. The extra weight on rare classes just added noise to the gradients.

## Experiment 9 (v9.0) -> Tell the nutrition predictor what food it's looking at
What: We feed the predicted food class probabilities (e.g. "80% chance this is pizza, 15% ramen...") as extra input to the nutrition predictor (regressor), alongside the image features. The idea: if the model knows it's looking at sushi, it should anchor fat predictions near sushi's typical range (~3g) rather than guessing from scratch.
Result: Mixed. Carbs MAE improved by 4.3% (best carbs result so far). Low-value biases improved: sushi fat bias was cut in half. But Median MAPE got slightly worse on all 4 nutrients.
Conclusion: Knowing the food class helps with rank-ordering predictions (correlations improved) and with extreme low-value cases (sushi, apple), but adds a small amount of noise to typical predictions. The class signal is most useful for carbs, which vary a lot between food types (apple ~25g, ramen ~85g). Not a clear enough winner to include in the final pipeline.

## Experiment 10 (v10.0) -> Penalize overestimation more than underestimation
What: We modified the loss function so that predicting too high is punished 2× more than predicting too low. We want to stop the model from overestimating fat on low-calorie foods like apple (true: 0.3g fat, predicted: ~1.8g).
Result: The low-value overestimation problem improved (apple fat bias: best ever at +0.34g). But everything else got worse: all 4 MAEs worse, all 4 Median MAPEs worse. High-calorie foods got badly under-predicted: fried chicken calorie bias went from -48 kcal to -95 kcal.
Conclusion: Foods that were already being under-predicted (fried chicken, ramen) got hurt badly. Failed experiment.

## Experiment 11 (v11.0) -> Train a separate model for each nutrient
What: Instead of one model predicting fat, protein, and carbs simultaneously (3 outputs), we train 3 completely independent models: one just for fat, one just for protein, one just for carbs. The reason is that fat, protein, and carbs have different visual cues and different distributions. Forcing one shared hidden layer to represent all three at once creates compromises. We also suspected they converge at different speeds and the joint model's early stopping was cutting off whichever nutrient needed more time.
Result: ALL 4 MAEs improved; the first experiment since v7.0 to achieve this. The convergence data confirmed the hypothesis: fat's model peaked at epoch 38, protein's at epoch 57, carbs' at epoch 32. The joint model had been stopping at epoch 50, which was too late for fat, too early for carbs. New best frozen model.
Conclusion: Nutrients benefit from independent training schedules.

## Experiment 12 (v12.0) -> Let the model decide which part of the image to focus on
What: Instead of treating every part of the image equally, we let the model learn to focus on the parts that matter most: ideally the food itself rather than the plate, table, or background. We do this by adding a small neural network layer that looks at each region of the image and assigns it a score (0 to 1) representing how important that region is.
Result: Worst result in the entire experiment series. Every single metric got worse.
Conclusion: EfficientNetB0 processes the image and its last layer outputs a 7×7 grid of features, so each cell covers a large chunk of the photo. The model can't really pinpoint "this is food, this is background" at that scale. Also, it seems that averaging all regions equally was actually helping the model stay robust; it didn't matter where in the frame the food appeared. Once we removed that, the model started overfitting to specific spatial patterns in the training photos that didn't generalize to new ones. Failed experiment.
