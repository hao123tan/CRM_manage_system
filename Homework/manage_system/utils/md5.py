import hashlib
def gen_md5(origin):
    '''
    md5加密
    :param origin:
    :return:
    '''
    ha = hashlib.md5()
    ha.update(origin.encode('utf-8'))
    return ha.hexdigest()