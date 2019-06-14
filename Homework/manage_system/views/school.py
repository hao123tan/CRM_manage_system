
from stark.service.v1 import StarkHandler



class SchoolHandler(StarkHandler):
    rbac = True
    list_display = ['title']
