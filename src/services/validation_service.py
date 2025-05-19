def validate_update_values(input):
    acc = int(input["acceleration"])
    vel = int(input["velocity"])
    
    if (vel < 0) or acc < 0:
        return False
    
    return True