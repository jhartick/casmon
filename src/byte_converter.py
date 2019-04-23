#!/bin/python2
import argparse
import math


def byte_converter():
    options = parse_options()
    result = ByteConverter.convert(options.value, options._from, options.to, precision=options.precision)
    if options.output is True:
        print(result)
    return result
    # print([k for k,v in Binary.units.items.iteritems()])
    # return result


def parse_options():
    """
    Parse the arguments this script was called with.

    :return: Options as Namespace
    """
    global parser
    parser = argparse.ArgumentParser(
        description='Perform numeral system and unit conversions.',
        formatter_class=argparse.RawTextHelpFormatter  # Enable multiline help Strings
    )
    parser.add_argument(
        '-v', '--value',
        dest='value',
        type=int,
        required=True,
        help='Number to be converted'
    )
    parser.add_argument(
        '-f', '--from',
        dest='_from',
        type=str,
        required=True,
        help='Current number unit'
    )
    parser.add_argument(
        '-t', '--to',
        dest='to',
        type=str,
        # choices=[ns.__name__ for ns in NumeralSystem.__subclasses__()],
        required=True,
        help='Required number unit'
    )
    parser.add_argument(
        '-o', '--output',
        dest='output',
        required=False,
        action="store_true",
        help='Output result to stdout'
    )
    parser.add_argument(
        '-p', '--precision',
        dest='precision',
        type=int,
        required=False,
        help='The precision level of the result (number of fractional digits)'
    )
    """
    parser.add_argument(
        '-ft',
        dest='from_type',
        choices=[unit.items for unit in [ns.units for ns in [sc for sc in NumeralSystem.__subclasses__()]]],
        required=True,
        help='Current numeral system'
    )
    parser.add_argument(
        '-tt',
        dest='to_type',
        choices=[unit.items for unit in [ns.units for ns in [sc for sc in NumeralSystem.__subclasses__()]]],
        required=True,
        help='Required numeral system'
    )
    """
    return parser.parse_args()


def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        raise ValueError


def enum(*sequential, **named):
    """
    Enum backport for Python2.x

    Usage: myenum = enum('KIB', 'MIB'
    Access: myenum.KIB

    :param type: Object type (required for later checking)
    :param sequential:
    :param named:
    :return: Enum
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse

    @staticmethod
    def from_string(text):
        return enums.get(text)

    enums['from_string'] = from_string
    enums['items'] = [i for i in sequential]
    return type('Enum', (), enums)


class NumeralSystem(object):
    """ Base Class for creating numeral systems """
    def __init__(self):
        pass


class Decimal(NumeralSystem):
    """ Decimal numeral system """
    base = 1000
    units = enum('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')

    def __init__(self):
        NumeralSystem.__init__(self)


class Binary(NumeralSystem):
    """ Binary numeral system """
    base = 1024
    units = enum('B', 'KIB', 'MIB', 'GIB', 'TIB', 'PIB', 'EIB', 'ZIB', 'YIB')

    def __init__(self):
        NumeralSystem.__init__(self)


class ByteConverter(object):
    """ Class for performing unit conversions between the numeral systems """
    def __init__(self):
        pass

    @staticmethod
    def convert(value, from_type, to_type, _from=None, to=None, precision=None):
        """
        Converts a number to the desired numeral system and unit.

        :param value: Value to be converted
        :param _from: Current numeral system
        :param to: Required numeral system
        :param from_type: Current unit of the number (case insensitive)
                          e.g. 'MIB' or Binary.units.MIB
        :param to_type: Required unit of the number (case insensitive)
                        e.g. 'mb' or Decimal.units.MB
        :param precision:   Amount of fractional digits. (e.g: precision = 3 -> result = 64.135)
                            The last digit is rounded up.
        :return: The result of the conversion
        """

        # Omitting the numeral system is allowed but results in slightly worse execution performance.
        if _from is None:
            _from = ByteConverter.get_ns_from_unit(from_type)
        else:
            if _from not in NumeralSystem.__subclasses__():
                raise NotImplementedError("Unknown numeral system.")
        if to is None:
            to = ByteConverter.get_ns_from_unit(to_type)
        else:
            if to not in NumeralSystem.__subclasses__():
                raise NotImplementedError("Unknown numeral system.")

        # Allow specification of data unit as str instead of enforcing the specification over the enum
        # e.g.: 'mib' | 'MB'    instead of    Binary.units.MIB | Binary.units.MB
        if type(from_type) is str:
            from_type = from_type.upper()
            from_type = _from.units.from_string(from_type)
        if type(to_type) is str:
            to_type = to_type.upper()
            to_type = to.units.from_string(to_type)

        _bytes = ByteConverter._to_bytes(float(value), from_type, _from.base)
        multitude = ByteConverter._to_multitude(_bytes, to_type, to.base)
        if precision is not None:
            precision = math.pow(10, precision)
            multitude = math.ceil(multitude*precision)/precision
        return multitude

    @staticmethod
    def _to_bytes(value, iter_count, base):
        """
        Convert a value to bytes

        :param value:
        :param iter_count: The number of iterations required
        :param base: The numeral system base
        :return: The value in bytes
        """
        for i in range(0, iter_count):
            value = float(value) * float(base)
        return value

    @staticmethod
    def _to_multitude(value, iter_count, base):
        """
        Convert a byte value to a higher order of magnitude

        :param value:
        :param iter_count: The number of iterations required
        :param base: The numeral system base
        :return: The value in the required order of multitude
        """
        for i in range(0, iter_count):
            value = float(value) / float(base)
        return value

    @staticmethod
    def get_ns_from_unit(unit):
        """
        Retrieve numeral system from unit str

        :param unit: The unit as str
        :return: The numeral system class
        :raise NotImplementedError: If the numeral system could not be identified.
        """
        unit = unit.upper()
        for ns in NumeralSystem.__subclasses__():
            if type(unit) is str:
                if unit in ns.units.items:
                    return ns
            else:
                if unit in ns.units.reverse_mapping:
                    return ns
        raise NotImplementedError("Unknown numeral system.")


if __name__ == '__main__':
    byte_converter()
