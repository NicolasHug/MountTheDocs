import math

import pytest
import sklearn
from sklearn import pipeline
from sklearn.feature_extraction.text import CountVectorizer
import sklearn.tree
import matplotlib
import matplotlib.pyplot as plt
import pandas
import numpy

from mount_the_docs import _import_obj, APIDocReader


@pytest.mark.parametrize(
    "path, expected_obj",
    [
        ("math", math),
        ("math.exp", math.exp),
        ("sklearn", sklearn),
        ("sklearn.pipeline", sklearn.pipeline),
        ("sklearn.pipeline.Pipeline", sklearn.pipeline.Pipeline),
        ("sklearn.tree", sklearn.tree),
        ("sklearn.tree.DecisionTreeClassifier", sklearn.tree.DecisionTreeClassifier),
        ("sklearn.feature_extraction.text.CountVectorizer", CountVectorizer),
        ("pandas", pandas),
        ("pandas.DataFrame", pandas.DataFrame),
        ("numpy", numpy),
        ("numpy.zeros", numpy.zeros),
        ("matplotlib", matplotlib),
        ("matplotlib.pyplot", plt),
        ("NotAPackage", None),
        ("sklearn.notAGoodName", None),
        ("sklearn..pipeline", None),
    ],
)
def test_import_obj(path, expected_obj):
    assert _import_obj(path) is expected_obj


@pytest.mark.parametrize(
    "package, path, some_attributes",
    [
        ("sklearn", "/", ["decomposition", "set_config", "tree"]),
        ("sklearn", "/linear_model", ["LogisticRegression", "Lasso"]),
        ("matplotlib", "/", ["pyplot"]),
    ],
)
def test_readdir(package, path, some_attributes):
    # Note: matplotlib.pyplot should fail because it's not in __init__ but it
    # works here because it was imported before
    api = APIDocReader(package)
    assert all(attr in api.readdir(path, 0) for attr in some_attributes)


@pytest.mark.parametrize(
    "partial, expected_path",
    [
        ("/", "sklearn"),
        ("/pipeline", "sklearn.pipeline"),
        ("/pipeline/make_pipeline", "sklearn.pipeline.make_pipeline"),
    ],
)
def test_obj_path(partial, expected_path):

    assert APIDocReader("sklearn")._get_obj_path(partial) == expected_path


@pytest.mark.parametrize(
    "partial, doc_part",
    [
        ("/", ""),
        ("/pipeline", ""),
        ("/pipeline/make_pipeline", "Construct a Pipeline from the given estimators"),
    ],
)
def test_get_docstring(partial, doc_part):

    docstring = APIDocReader("sklearn")._get_docstring(partial).decode("UTF-8")
    if not doc_part:
        assert not docstring
    assert doc_part in docstring
