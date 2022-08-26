# import sys
# sys.path.append('..')
# from Models import numericalWrapperForText
# import pytest
# import numpy as np
# from sklearn.dummy import DummyClassifier
# from fastapi.testclient import TestClient
# from hypothesis import given, assume
# from hypothesis.strategies import text, integers, lists


#@given(min_n=integers(min_value=1), max_n=integers(min_value=1))
#def test_numericalWrapperForText_methods():
    #text_list = ["One Cent, Two Cents, Old Cent, New Cent: All About Money"]
    #assume(min_n <= max_n)
    #nwft = numericalWrapperForText.NumericalWrapperForText(ngram_min_n = 1, ngram_max_n = 2, numeric_classifier=DummyClassifier)
    #random_y = np.random.random_sample(size = len(text_list))
    #nwft.fit(text_list, random_y)