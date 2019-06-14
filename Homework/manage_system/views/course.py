from stark.service.v1 import StarkHandler


class CourseHandler(StarkHandler):
    list_display = ['name',StarkHandler.display_edit_del]