import subprocess


def construct_get_request_params(obj): 
    data_string = ""
    for i, (key, val) in enumerate(obj.items()):
        if i == 0:
            data_string += f"?{key}={val}"
        else:
            data_string += f"&{key}={val}"
    
    return data_string



def make_request(url, obj=None, method="GET"):
    try:
        if obj:
            data = construct_get_request_params(obj)
            url = url+data
            a=1
        return subprocess.run(["curl", "-X", method,url], capture_output=True, text=True)
    except Exception as e:
        raise