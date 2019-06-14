from stark.service.v1 import site
from manage_system import models
from manage_system.views.userinfo import UserInfoHandler
from manage_system.views.depart import DepartmentHandler
from manage_system.views.school import SchoolHandler
from manage_system.views.course import CourseHandler
from manage_system.views.class_list import ClassListHandler
from manage_system.views.public_customer import PublicCustomerHandler
from manage_system.views.private_customer import PrivateCustomerHandler
from manage_system.views.payment_record import PaymentRecordHandler
from manage_system.views.check_payment_record import CheckPaymentRecordHandler
from manage_system.views.consult_record import ConsultRecordHandler
from manage_system.views.student import StudentHandler
from manage_system.views.course_record import CourseRecordHandler
from manage_system.views.score_record import ScoreRecordHandler
from manage_system.views.homeworkteacher import HomeWorkTeacherHandler
from manage_system.views.homeworkstudent import HomeworkStudentHandler


site.register(models.UserInfo,UserInfoHandler)
site.register(models.Department,DepartmentHandler)
site.register(models.School,SchoolHandler)
site.register(models.Course,CourseHandler)
site.register(models.Classlist,ClassListHandler)
site.register(models.Customer,PublicCustomerHandler,'pub')
site.register(models.Customer,PrivateCustomerHandler,'priv')
site.register(models.PaymentRecord,PaymentRecordHandler)
site.register(models.PaymentRecord, CheckPaymentRecordHandler, 'check')
site.register(models.ConsultRecord,ConsultRecordHandler)
site.register(models.Student, StudentHandler)
site.register(models.ScoreRecord, ScoreRecordHandler)
site.register(models.CourseRecord, CourseRecordHandler,'normal')
site.register(models.CourseRecord, HomeWorkTeacherHandler,'homework')
site.register(models.HomeWorkStudentRecord,HomeworkStudentHandler)



