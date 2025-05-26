def get_register_values(data):
    left_data, right_data = data
    left_vals = []
    right_vals = []
    for register in left_data.registers:
        left_vals.append(register)

    for register in right_data.registers:
        right_vals.append(register)
        
    return (left_vals, right_vals)
    