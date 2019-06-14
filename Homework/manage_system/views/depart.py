from stark.service.v1 import StarkHandler



class DepartmentHandler(StarkHandler):
    list_display = ['title', StarkHandler.display_edit_del]