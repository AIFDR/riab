import os
import types

TESTDATA = os.path.join(os.environ['RIAB_HOME'],
                                   'riab_data', 'risiko_test_data')



def _same_API(X, Y, exclude=[]):
    """Check that public methods of X also exist in Y
    """

    for name in dir(X):

        # Skip internal symbols
        if name.startswith('_'):
            continue

        # Skip explicitly excluded methods
        if name in exclude:
            continue

        # Check membership of methods
        attr = getattr(X, name)
        if isinstance(attr, types.MethodType):
            if name not in dir(Y):
                msg = 'Method %s of %s was not found in %s' % (name, X, Y)
                raise Exception(msg)


def same_API(X, Y, exclude=[]):
    """Check that public methods of X and Y are the same
    """

    _same_API(X, Y, exclude=exclude)
    _same_API(Y, X, exclude=exclude)

    return True
