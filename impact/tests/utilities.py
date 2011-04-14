import os

TESTDATA = os.path.join(os.environ['RIAB_HOME'],
                                   'riab_data', 'risiko_test_data')

def same_API(X, Y):
    """Check that attributes and methods of X and Y are the same
    """


    for method in dir(X):
        if method not in dir(Y):
            msg = 'Method %s of %s was not found in %s' % (method, X, Y)
            raise Exception(msg)


    print
    print dir(X)
    print dir(Y)


    print X.__dict__
    print Y.__dict__
