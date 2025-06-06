from helpers.motor_api_helper import clamp_target_revs
from settings.motors_config import MotorConfig

config = MotorConfig()

def test_urev_clamp():
    ### In range
    assert clamp_target_revs(20.0, 20.0, config) == ((0, 20), (0, 20))
    assert clamp_target_revs(21.0, 19.0, config) == ((0, 21), (0, 19))
    assert clamp_target_revs(21.5, 19.25, config) == ((32768, 21), (16384, 19))
    assert clamp_target_revs(21.25, 19.5, config) == ((16384, 21), (32768, 19))
    assert clamp_target_revs(21.75, 19.5, config) == ((16384+32768, 21), (32768, 19))
    assert clamp_target_revs(21.99999999999, 19.5, config) == ((65535, 21), (32768, 19))
    assert clamp_target_revs(21.99999999999, 19.99999999999, config) == ((65535, 21), (65535, 19))
    assert clamp_target_revs(21.0, 19.99999999999, config) == ((0, 21), (65535, 19))
    
    ### Overshoot
    assert clamp_target_revs(300.99999999999, 20.5, config) == ((61406, 28), (32768, 20))
    assert clamp_target_revs(300.25, 20.5, config) == ((16384, 28), (32768, 20))
    assert clamp_target_revs(300.99999999999, 20.25, config) == ((61406, 28), (16384, 20))
    assert clamp_target_revs(300.99999999999, 28.99999999999, config) == ((61406, 28), (61406, 28))
    assert clamp_target_revs(16.25, 300.50, config) == ((16384, 16), (32768, 28))
    assert clamp_target_revs(16.25, 300.99999999999, config) == ((16384, 16), (61406, 28))
    
    ### Undershoot
    assert clamp_target_revs(-300.01, 0.01, config) == ((25801, 0), (25801, 0))
    assert clamp_target_revs(-300.01, 10.0, config) == ((25801, 0), (0, 10))
    assert clamp_target_revs(-300.01, 28.0, config) == ((25801, 0), (0, 28))
    assert clamp_target_revs(-300.01, 28.99999999999, config) == ((25801, 0), (61406, 28))
    assert clamp_target_revs(20.25, -300.01, config) == ((16384, 20), (25801, 0))
    assert clamp_target_revs(28.25, -300.01, config) == ((16384, 28), (25801, 0))
    assert clamp_target_revs(29.25, -300.01, config) == ((16384, 28), (25801, 0))
    assert clamp_target_revs(29.99999999999, -300.01, config) == ((61406, 28), (25801, 0))
    assert clamp_target_revs(29.99999999999, -300.5, config) == ((61406, 28), (32768, 0))
    
    
    #61406
    #25801
clamp_target_revs(29.99999999999, -300.5, config) == ((61406, 28), (32768, 0))