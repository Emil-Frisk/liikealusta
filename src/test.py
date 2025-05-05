high_decimal = 2560 >> 7

a = 10
lower_decimal = 15
result = high_decimal | lower_decimal

a = 20
# print(moi)
velocity_left = high_decimal >> 8
b = 10

def bit_high_low(number, low_bit):
    bit_mask = (2**low_bit) - 1
    register_val_high = number >> low_bit
    register_val_low = number & bit_mask
    return (register_val_high, register_val_low)

result = bit_high_low(2560, 7)
result2 = bit_high_low(40, 4)

a = 10

