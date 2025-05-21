from utils.utils import convert_vel_rpm_revs, convert_to_revs, convert_acc_rpm_revs

async def set_motor_values(values,clients):
    try:
        if 'velocity' in values:
            (velocity_whole, velocity_decimal) = convert_vel_rpm_revs(values["velocity"])
            if not await clients.set_analog_vel_max(velocity_decimal, velocity_whole):
                print("Velocity not uptaded successfully")
        if 'acceleration' in values:
            (acc_decimal, acc_whole) = convert_acc_rpm_revs(values["acceleration"])
            if not await clients.set_analog_acc_max(acc_decimal, acc_whole):
                print("Acceleration not uptaded successfully")
    except Exception as e:
        print(e)

async def configure_motor(clients, config):
    """ Tries to initialize the motors with values returns true if succesful """
    await clients.set_host_command_mode(0)
    await clients.set_ieg_mode(65535)
    homed = await clients.home()
    if homed: 
        ## Prepare motor parameters for operation
        ### MAX POSITION LIMITS FOR BOTH MOTORS | 147 mm
        if not await clients.set_analog_pos_max(61406, 28):
            return False

        ### MIN POSITION LIMITS FOR BOTH MOTORS || 2 mm
        if not await clients.set_analog_pos_min(25801, 0):
            return False

        ### Velocity whole number is in 8.8 where decimal is in little endian format,
        ### meaning smaller bits come first, so 1 rev would be 2^8
        (velocity_whole, velocity_decimal) = convert_vel_rpm_revs(config.VEL)
        if not await clients.set_analog_vel_max(velocity_decimal, velocity_whole):
            return False

        ### UACC32 whole number split in 12.4 format
        (acc_whole, acc_decimal) =convert_acc_rpm_revs(config.ACC)
        if not await clients.set_analog_acc_max(acc_decimal, acc_whole):
            return False

        ## Analog input channel set to use modbusctrl (2)
        if not await clients.set_analog_input_channel(2):
            return False

        response = await clients.get_modbuscntrl_val()
        if not response:
            return False
        (position_client_left, position_client_right) = response

        # modbus cntrl 0-10k
        if not await clients.set_analog_modbus_cntrl((position_client_left, position_client_right)):
            return False

        # # Finally - Ready for operation
        if not await clients.set_host_command_mode(config.ANALOG_POSITION_MODE):
            return False

        # Enable motors
        if not await clients.set_ieg_mode(2):
            return False