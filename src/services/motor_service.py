from services.cleaunup import cleanup
from utils.utils import convert_vel_rpm_revs, convert_to_revs, convert_acc_rpm_revs

async def set_motor_values(values,clients):
    if 'velocity' in values:
        (velocity_whole, velocity_decimal) = convert_vel_rpm_revs(values.velocity)
        if not await clients.set_analog_vel_max(velocity_decimal, velocity_whole):
            cleanup()
    if 'acceleration' in values:
        (acc_decimal, acc_whole) = convert_acc_rpm_revs(values.acceleration)
        if not await clients.set_analog_acc_max(acc_decimal, acc_whole):
            cleanup()
    
    

async def configure_motor(clients, config):
    await clients.set_host_command_mode(0)
    ### TODO - posita myöhemmin kun fault pollerin toimimaan
    await clients.set_ieg_mode(65535)
    homed = await clients.home()
    if homed: 
        ## Prepare motor parameters for operation
        ### If any of them are unsuccesful -> cleanup and shutdown

        ### MAX POSITION LIMITS FOR BOTH MOTORS | 147 mm
        if not await clients.set_analog_pos_max(61406, 28):
            cleanup()

        ### MIN POSITION LIMITS FOR BOTH MOTORS || 2 mm
        if not await clients.set_analog_pos_min(25801, 0):
            cleanup()

        ### Velocity whole number is in 8.8 where decimal is in little endian format,
        ### meaning smaller bits come first, so 1 rev would be 2^8
        (velocity_whole, velocity_decimal) = convert_vel_rpm_revs(config.VEL)
        if not await clients.set_analog_vel_max(velocity_decimal, velocity_whole):
            cleanup()

        ### UACC32 whole number split in 12.4 format
        (acc_whole, acc_decimal) =convert_acc_rpm_revs(config.ACC)
        if not await clients.set_analog_acc_max(acc_decimal, acc_whole):
            cleanup()

        ## Analog input channel set to use modbusctrl (2)
        if not await clients.set_analog_input_channel(2):
            cleanup()

        response = await clients.get_modbuscntrl_val()
        if not response:
            cleanup()
        (position_client_left, position_client_right) = response

        # modbus cntrl 0-10k
        if not await clients.set_analog_modbus_cntrl((position_client_left, position_client_right)):
            cleanup()

        # # Finally - Ready for operation
        if not await clients.set_host_command_mode(config.ANALOG_POSITION_MODE):
            cleanup()

        # Enable motors
        if not await clients.set_ieg_mode(2):
            cleanup()