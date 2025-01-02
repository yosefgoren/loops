# Fewshot Context Validation
First tried the original prompt with more explicit system description and got the following results:
* With 0 examples (exp 11):
    - success rate: 0.28205128205128205
    - 1dist rate: 0.717948717948718
    - average bias: 0.28205128205128205
    - average dist: 1.0512820512820513

* With 1 example (exp 3):
    - success rate: 0.3076923076923077
    - 1dist rate: 0.717948717948718
    - average bias: 0.9487179487179487
    - average dist: 1.1025641025641026

* With 2 examples (exp 2):
    - success rate: 0.3333333333333333
    - 1dist rate: 0.6666666666666666
    - average bias: 0.48717948717948717
    - average dist: 1.1025641025641026

* With 5 examples (exp 1):
    - success rate: 0.28205128205128205
    - 1dist rate: 0.717948717948718
    - average bias: 0.6923076923076923
    - average dist: 1.1538461538461537

Then tried making the system prompt shorter and simpler while keeping the context the same and got:
* With 0 examples (exp 12):
    - success rate: 0.3333333333333333
    - 1dist rate: 0.7948717948717948
    - average bias: -0.10256410256410256
    - average dist: 0.9230769230769231

* With 1 example (exp 4):
    - success rate: 0.2564102564102564
    - 1dist rate: 0.6410256410256411
    - average bias: 1.1794871794871795
    - average dist: 1.2307692307692308

* With 2 examples (exp 6):
    - success rate: 0.3333333333333333
    - 1dist rate: 0.7435897435897436
    - average bias: 0.46153846153846156
    - average dist: 0.9743589743589743

* With 5 examples (exp 5):
    - success rate: 0.358974358974359
    - 1dist rate: 0.6923076923076923
    - average bias: 0.4358974358974359
    - average dist: 1.0512820512820513

Then changed the system prompt again to specify the code snippets are from NPB-OMP and compared to the performance of the benchmark with 'S' class and no parallelization. The results were:
* With 0 examples (exp 10):
    - success rate: 0.3333333333333333
    - 1dist rate: 0.7435897435897436
    - average bias: 0.3333333333333333
    - average dist: 0.9487179487179487

* With 1 example (exp 9):
    - success rate: 0.3076923076923077
    - 1dist rate: 0.6923076923076923
    - average bias: 1.0
    - average dist: 1.1538461538461537

* With 2 examples (exp 7):
    - success rate: 0.41025641025641024
    - 1dist rate: 0.717948717948718
    - average bias: 0.48717948717948717
    - average dist: 0.9487179487179487

* With 5 examples (exp 8):
    - success rate: 0.358974358974359
    - 1dist rate: 0.6923076923076923
    - average bias: 0.41025641025641024
    - average dist: 1.0256410256410255