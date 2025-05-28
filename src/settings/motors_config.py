from dataclasses import dataclass

@dataclass
class MotorConfig:
    SLAVE_ID: int = 1
    
    ### INPUT EVENTS
    IEG_MODE: int = 4316
    IEG_MOTION: int = 4317 # stop 2^2

    ### OUTPUT ADDRESSES
    OEG_STATUS: int = 104
    
    ### ANALOG POS
    ANALOG_POSITION_MINIMUM = 7102
    ANALOG_POSITION_MAXIMUM = 7104
    ANALOG_VEL_MAXIMUM = 7106
    ANALOG_ACCELERATION_MAXIMUM = 7108
    ANALOG_INPUT_CHANNEL = 7101
    ANALOG_MODBUS_CNTRL = 7188

    PFEEDBACK_POSITION = 378
    IPEAK = 5108
    RECENT_FAULT_ADDRESS: int = 846 #Coms bit 10 -> 2^10
    VFEEDBACK_VELOCITY: int = 361
    SYSTEM_COMMAND: int = 4001

    ### Telemetry registers (high)
    ICONTINUOUS = 564
    ACTUATOR_TMP = 15
    BOARD_TMP = 11
    VBUS = 570 # 11.21

    ### OPERATION MODES
    COMMAND_MODE = 4303
    DISABLED = 0
    DIGITAL_INPUT = 1
    ANALOG_POSITION_MODE = 2
    
    ## Percentile = x - pos_min / (pos_max - pos_min)
    POS_MIN_REVS = 0.393698024
    POS_MAX_REVS = 28.93700787401574803149606299212
    
    ### Register values
    HOME_VALUE = 256
    STOP_VALUE = 4
    RESTART_VALUE = 1
    RESET_FAULT_VALUE = 32768
    ENABLE_MAINTAINED_VALUE = 2
    ### 2 tells the drivers to use simulated analog input
    ANALOG_MODBUS_CNTRL_VALUE = 2

    ###
    MODBUSCTRL_MAX = 10000
    ACC = 123  
    VEL = 321
    