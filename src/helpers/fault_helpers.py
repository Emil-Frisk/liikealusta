from utils.utils import is_nth_bit_on
from constants.fault_codes import CRITICAL_FAULTS, ABSOLUTE_FAULTS

def has_faulted(data):
    left, right = data
    return (is_nth_bit_on(3, left), is_nth_bit_on(3, right))

def is_critical_fault(data):
    left, right = data 
    if not left in CRITICAL_FAULTS and not right in CRITICAL_FAULTS:
        return False
    return True

def is_absolute_fault(data):
    left, right = data
    if not left in ABSOLUTE_FAULTS and not right in ABSOLUTE_FAULTS:
        return False
    return True
