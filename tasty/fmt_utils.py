# -*- coding: utf-8 -*-
import sys
import tasty.types

def format_output(attribute, desc="", fmt=None):
    if desc:
        if fmt:
            if isinstance(attribute, tasty.types.Plain):
                return u"{0}: {1:{2}}".format(desc, long(attribute), fmt)
            elif isinstance(attribute, tasty.types.Vec):
                return u"{0}: {1:{2}}".format(desc, attribute, fmt)
            elif isinstance(attribute, basestring):
                return u"{0}: {1!s}".format(desc, attribute)
        else:
            if isinstance(attribute, tasty.types.Plain):
                return u"{0}: {1}".format(desc, long(attribute))
            elif isinstance(attribute, tasty.types.Vec):
                return u"{0}: {1}".format(desc, str(attribute))
            else:
                return u"{0}: {1!s}".format(desc, attribute.decode(sys.getfilesystemencoding()))
    else:
        if fmt and isinstance(attribute, tasty.types.Plain):
            return u"{0:{1}}".format(long(attribute), fmt)
        if fmt and isinstance(attribute, tasty.types.Vec):
            return u"{0:{1}}".format(attribute, fmt)
        else:
            return attribute
